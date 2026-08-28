import pytest
from datetime import datetime, timezone
from app.audit.repository import PostgresAuditRepository, InMemoryAuditRepository
from app.approval.repository import PostgresApprovalRepository, InMemoryApprovalRepository
from app.security.credentials import APICredentialRepository, RoleEnum
from app.security.idempotency import IdempotencyManager
from app.db.session import check_db_connectivity, async_session_factory
from app.db.models import AuditLogModel, ApprovalTicketModel
from sqlalchemy import select
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_postgres_db_connectivity_check():
    """Verify that check_db_connectivity returns a boolean status."""
    is_ready = await check_db_connectivity()
    assert isinstance(is_ready, bool)


@pytest.mark.asyncio
async def test_postgres_audit_persistence_and_restart():
    """Verify audit records are stored in PostgreSQL audit_logs table and persist across repository restarts."""
    if not await check_db_connectivity():
        pytest.skip("PostgreSQL database unavailable or unreachable")

    raw_in_mem = InMemoryAuditRepository()
    repo1 = PostgresAuditRepository(fallback_repo=raw_in_mem)
    req_id = f"req_audit_{int(datetime.now(timezone.utc).timestamp())}"

    # 1. Save audit log
    await repo1.save_audit_log(
        request_id=req_id,
        user_id="user_test_audit",
        intent="SEARCH_DOCUMENT",
        resource="sec_doc.pdf",
        ai_risk="LOW",
        policy_risk="LOW",
        final_decision="ALLOW",
        provider="test_provider",
        fallback_used=False,
        latency_ms=12.5,
        tenant_id="tenant_audit_test",
    )

    # 2. Verify row exists in PostgreSQL audit_logs table
    async with async_session_factory() as session:
        stmt = select(AuditLogModel).where(AuditLogModel.request_id == req_id)
        res = await session.execute(stmt)
        db_log = res.scalar_one_or_none()
        assert db_log is not None
        assert db_log.tenant_id == "tenant_audit_test"
        assert db_log.user_id == "user_test_audit"

    # 3. Simulate repository restart (fresh instance with empty fallback memory)
    fresh_in_mem = InMemoryAuditRepository()
    repo2 = PostgresAuditRepository(fallback_repo=fresh_in_mem)
    events = await repo2.list_audit_events(tenant_id="tenant_audit_test", request_id=req_id)
    assert len(events) >= 1
    assert events[0]["request_id"] == req_id
    assert events[0]["tenant_id"] == "tenant_audit_test"


@pytest.mark.asyncio
async def test_postgres_audit_tenant_isolation():
    """Verify audit records are strictly isolated by server-side tenant_id."""
    raw_in_mem = InMemoryAuditRepository()
    repo = PostgresAuditRepository(fallback_repo=raw_in_mem)
    req_id_a = f"req_t_a_{int(datetime.now(timezone.utc).timestamp())}"
    req_id_b = f"req_t_b_{int(datetime.now(timezone.utc).timestamp())}"

    await repo.save_audit_log(
        request_id=req_id_a,
        user_id="user_a",
        intent="READ_DATA",
        resource="res_a",
        ai_risk="LOW",
        policy_risk="LOW",
        final_decision="ALLOW",
        provider="gemini",
        fallback_used=False,
        latency_ms=10.0,
        tenant_id="tenant_alpha",
    )

    await repo.save_audit_log(
        request_id=req_id_b,
        user_id="user_b",
        intent="READ_DATA",
        resource="res_b",
        ai_risk="LOW",
        policy_risk="LOW",
        final_decision="ALLOW",
        provider="gemini",
        fallback_used=False,
        latency_ms=10.0,
        tenant_id="tenant_beta",
    )

    # tenant_alpha list must not see tenant_beta record
    events_a = await repo.list_audit_events(tenant_id="tenant_alpha")
    a_req_ids = [e["request_id"] for e in events_a]
    assert req_id_a in a_req_ids
    assert req_id_b not in a_req_ids


@pytest.mark.asyncio
async def test_postgres_approval_persistence_and_restart():
    """Verify approval tickets are stored in PostgreSQL and persist across repository restarts."""
    if not await check_db_connectivity():
        pytest.skip("PostgreSQL database unavailable or unreachable")

    raw_in_mem = InMemoryApprovalRepository()
    repo1 = PostgresApprovalRepository(fallback_repo=raw_in_mem)
    appr_id = f"appr_test_{int(datetime.now(timezone.utc).timestamp())}"

    # 1. Create approval ticket
    ticket1 = await repo1.create_ticket(
        approval_id=appr_id,
        request_id="req_appr_123",
        requester_id="user_req",
        intent="DELETE_DATA",
        resource="table_sensitive",
        policy_risk="HIGH",
        tenant_id="tenant_appr_test",
    )
    assert ticket1.status == "PENDING"

    # 2. Verify row exists in PostgreSQL approval_tickets table
    async with async_session_factory() as session:
        stmt = select(ApprovalTicketModel).where(ApprovalTicketModel.approval_id == appr_id)
        res = await session.execute(stmt)
        db_ticket = res.scalar_one_or_none()
        assert db_ticket is not None
        assert db_ticket.tenant_id == "tenant_appr_test"
        assert db_ticket.status == "PENDING"

    # 3. Simulate repository restart (fresh instance with empty memory)
    fresh_in_mem = InMemoryApprovalRepository()
    repo2 = PostgresApprovalRepository(fallback_repo=fresh_in_mem)
    fetched_ticket = await repo2.get_ticket(appr_id, tenant_id="tenant_appr_test")
    assert fetched_ticket is not None
    assert fetched_ticket.approval_id == appr_id
    assert fetched_ticket.tenant_id == "tenant_appr_test"

    # 4. Update approval status
    updated_ticket = await repo2.update_ticket_status(appr_id, "APPROVED", approver_id="user_manager", tenant_id="tenant_appr_test")
    assert updated_ticket.status == "APPROVED"

    # 5. Verify update in PostgreSQL
    async with async_session_factory() as session:
        stmt = select(ApprovalTicketModel).where(ApprovalTicketModel.approval_id == appr_id)
        res = await session.execute(stmt)
        db_updated = res.scalar_one_or_none()
        assert db_updated.status == "APPROVED"
        assert db_updated.approver_id == "user_manager"


@pytest.mark.asyncio
async def test_postgres_approval_tenant_isolation():
    """Verify approval tickets enforce strict tenant isolation (cross-tenant access returns HTTP 403)."""
    raw_in_mem = InMemoryApprovalRepository()
    repo = PostgresApprovalRepository(fallback_repo=raw_in_mem)
    appr_id = f"appr_iso_{int(datetime.now(timezone.utc).timestamp())}"

    await repo.create_ticket(
        approval_id=appr_id,
        request_id="req_iso_1",
        requester_id="user_iso",
        intent="DELETE_DATA",
        resource="table_iso",
        policy_risk="HIGH",
        tenant_id="tenant_iso_A",
    )

    # Attempting to access tenant_iso_A ticket from tenant_iso_B must raise HTTP 403
    with pytest.raises(HTTPException) as exc_info:
        await repo.get_ticket(appr_id, tenant_id="tenant_iso_B")
    assert exc_info.value.status_code == 403
    assert "Cross-tenant access forbidden" in exc_info.value.detail


@pytest.mark.asyncio
async def test_postgres_api_credential_persistence_and_no_plaintext():
    """Verify API credentials persist to PostgreSQL api_credentials table and never store plaintext keys."""
    if not await check_db_connectivity():
        pytest.skip("PostgreSQL database unavailable or unreachable")

    repo1 = APICredentialRepository()
    raw_key, record = await repo1.create_credential(
        tenant_id="tenant_cred_test",
        user_id="user_cred_test",
        name="Test Persistence Key",
        role=RoleEnum.OPERATOR,
    )

    # Plaintext raw_key must not be saved in record or hash
    assert raw_key != record.key_hash

    # Verify query by raw key works
    fetched = await repo1.get_by_raw_key(raw_key)
    assert fetched is not None
    assert fetched.credential_id == record.credential_id
    assert fetched.tenant_id == "tenant_cred_test"

    # Simulate repository restart
    repo2 = APICredentialRepository()
    fetched_after_restart = await repo2.get_by_raw_key(raw_key)
    assert fetched_after_restart is not None
    assert fetched_after_restart.credential_id == record.credential_id


@pytest.mark.asyncio
async def test_postgres_idempotency_persistence():
    """Verify idempotency records persist and prevent duplicate executions."""
    if not await check_db_connectivity():
        pytest.skip("PostgreSQL database unavailable or unreachable")

    idem_mgr = IdempotencyManager()
    user_id = "user_idem_test"
    idem_key = f"idem_key_{int(datetime.now(timezone.utc).timestamp())}"
    payload = {"status": "executed", "data": "test_result"}

    # No initial record
    assert (await idem_mgr.get_record(user_id=user_id, idempotency_key=idem_key, tenant_id="tenant_idem")) is None

    # Save record
    await idem_mgr.save_record(user_id=user_id, idempotency_key=idem_key, result=payload, tenant_id="tenant_idem")

    # Immediate retrieval
    cached = await idem_mgr.get_record(user_id=user_id, idempotency_key=idem_key, tenant_id="tenant_idem")
    assert cached == payload

    # Re-instantiated manager (simulated restart)
    idem_mgr_fresh = IdempotencyManager()
    cached_after_restart = await idem_mgr_fresh.get_record(user_id=user_id, idempotency_key=idem_key, tenant_id="tenant_idem")
    assert cached_after_restart == payload
