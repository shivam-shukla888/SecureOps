import asyncio
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from app.security.rbac import RoleEnum, TenantUserContext
from app.security.credentials import credential_repo, hash_api_key
from app.approval.manager import approval_manager
from app.approval.repository import in_memory_approval_repo
from app.audit.repository import in_memory_audit_repo
from app.audit.security_events import SecurityEvent, SecurityEventType, SeverityEnum
from app.audit.siem import siem_manager, ConsoleSIEMExporter
from app.tools.integrations.document_service import document_service_adapter, DocumentSearchRequest
from app.db.safe_query import safe_db_adapter
from app.config import settings, validate_production_config


def test_credential_creation_rotation_and_revocation():
    # 1. Create Credential for Tenant A
    raw_key, record = credential_repo.create_credential(
        tenant_id="tenant_acme",
        user_id="user_acme_admin",
        name="Acme Admin Key",
        role=RoleEnum.ADMIN,
    )
    assert raw_key.startswith("secops_")
    assert record.tenant_id == "tenant_acme"

    # 2. Lookup Credential by Key
    fetched = credential_repo.get_by_raw_key(raw_key)
    assert fetched is not None
    assert fetched.credential_id == record.credential_id

    # 3. Rotate Credential
    new_raw_key, rotated_rec = credential_repo.rotate_credential(record.credential_id, tenant_id="tenant_acme")
    assert new_raw_key != raw_key
    assert credential_repo.get_by_raw_key(raw_key) is None  # Old key revoked
    assert credential_repo.get_by_raw_key(new_raw_key) is not None  # New key valid

    # 4. Revoke Credential
    credential_repo.revoke_credential(rotated_rec.credential_id, tenant_id="tenant_acme")
    assert credential_repo.get_by_raw_key(new_raw_key) is None  # Revoked key returns None


def test_cross_tenant_approval_access_blocked(client):
    # Create ticket in Tenant A
    ticket = asyncio.run(
        in_memory_approval_repo.create_ticket("appr_tenantA_1", "req1", "userA", "DELETE_DATA", "db", "HIGH", tenant_id="tenant_A")
    )

    # Attempt to fetch/approve ticket using Tenant B credentials
    raw_key_B, _ = credential_repo.create_credential("tenant_B", "userB_admin", "Tenant B Key", RoleEnum.ADMIN)
    headers_B = {"Authorization": f"Bearer {raw_key_B}"}

    # Cross-tenant GET /v1/approvals/appr_tenantA_1 -> 403 Forbidden
    resp = client.get(f"/v1/approvals/{ticket.approval_id}", headers=headers_B)
    assert resp.status_code == 403
    assert "Cross-tenant access forbidden" in resp.json()["error"]["message"]

    # Cross-tenant POST /v1/approvals/appr_tenantA_1/approve -> 403 Forbidden
    resp_approve = client.post(
        f"/v1/approvals/{ticket.approval_id}/approve",
        json={"approver_id": "userB_admin"},
        headers=headers_B,
    )
    assert resp_approve.status_code == 403


def test_rbac_role_permissions_enforced(client):
    # Create Viewer credential for Tenant A
    raw_key_viewer, _ = credential_repo.create_credential("tenant_A", "user_viewer", "Viewer Key", RoleEnum.VIEWER)
    headers_viewer = {"Authorization": f"Bearer {raw_key_viewer}"}

    # Viewer attempts to create credential -> 403 Forbidden
    resp_create = client.post(
        "/v1/credentials",
        json={"name": "Injected Key", "role": "ADMIN"},
        headers=headers_viewer,
    )
    assert resp_create.status_code == 403
    assert "RBAC Permission Denied" in resp_create.json()["error"]["message"]

    # Viewer attempts to list approvals -> 403 Forbidden
    resp_appr = client.get("/v1/approvals", headers=headers_viewer)
    assert resp_appr.status_code == 403

    # Viewer attempts to list audit events -> 200 OK
    resp_audit = client.get("/v1/audit/events", headers=headers_viewer)
    assert resp_audit.status_code == 200


def test_document_service_adapter_tenant_isolation():
    async def run():
        req_default = DocumentSearchRequest(query="audit", tenant_id="tenant_default")
        res_default = await document_service_adapter.search_documents(req_default)
        assert res_default["results_count"] == 1

        req_acme = DocumentSearchRequest(query="roadmap", tenant_id="tenant_acme")
        res_acme = await document_service_adapter.search_documents(req_acme)
        assert res_acme["tenant_id"] == "tenant_acme"

    asyncio.run(run())


def test_safe_database_query_adapter():
    async def run():
        # Valid table name & tenant_id -> OK
        rows = await safe_db_adapter.execute_safe_tenant_select("audit_logs", tenant_id="tenant_acme")
        assert len(rows) > 0
        assert rows[0]["tenant_id"] == "tenant_acme"

        # SQL injection table name attempt -> 400 Bad Request
        with pytest.raises(HTTPException) as exc:
            await safe_db_adapter.execute_safe_tenant_select("users; DROP TABLE users; --", tenant_id="tenant_acme")
        assert exc.value.status_code == 400
        assert "Invalid or unauthorized table name identifier" in exc.value.detail

    asyncio.run(run())


def test_siem_security_event_logging():
    async def run():
        event = SecurityEvent(
            event_type=SecurityEventType.PROMPT_INJECTION,
            severity=SeverityEnum.HIGH,
            tenant_id="tenant_acme",
            user_id="attacker",
            metadata={"detail": "Detected jailbreak prompt injection"},
        )
        await siem_manager.record_security_event(event)

        events = siem_manager.list_tenant_security_events(tenant_id="tenant_acme")
        assert len(events) > 0
        assert events[-1]["event_type"] == "PROMPT_INJECTION"

    asyncio.run(run())


def test_production_config_validation():
    # Development mode -> PASS
    validate_production_config()

    # Unsafe Production mode -> Fails startup
    with pytest.raises(RuntimeError) as exc:
        with patch.object(settings, "ENVIRONMENT", "production"):
            with patch.object(settings, "ALLOWED_OUTBOUND_HOSTS", []):
                validate_production_config()
    assert "ALLOWED_OUTBOUND_HOSTS policy cannot be empty in production" in str(exc.value)
