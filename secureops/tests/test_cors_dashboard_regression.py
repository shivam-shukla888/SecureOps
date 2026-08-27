import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.security.credentials import credential_repo
from app.security.rbac import RoleEnum


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_credentials():
    """Create test credential records for tenant isolation tests."""
    import asyncio
    async def _create():
        k1, r1 = await credential_repo.create_credential(
            tenant_id="tenant_cors_alpha",
            user_id="user_alpha",
            name="CORS Alpha Key",
            role=RoleEnum.ADMIN,
        )
        k2, r2 = await credential_repo.create_credential(
            tenant_id="tenant_cors_beta",
            user_id="user_beta",
            name="CORS Beta Key",
            role=RoleEnum.ADMIN,
        )
        return k1, r1, k2, r2

    return asyncio.run(_create())


def test_req_6a_health_check_returns_200(client):
    """A. GET /health returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_req_6b_dashboard_without_api_key_returns_401(client):
    """B. GET /v1/dashboard/summary without API key returns 401."""
    response = client.get("/v1/dashboard/summary")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["status_code"] == 401


def test_req_6c_6d_6e_11_options_dashboard_cors_preflight_success(client):
    """
    C. OPTIONS /v1/dashboard/summary with an allowed Origin returns a successful CORS preflight response.
    D. Preflight response contains Access-Control-Allow-Origin matching origin (not wildcard '*').
    E. Preflight does NOT require API authentication.
    11. Permanent regression test: OPTIONS /v1/dashboard/summary must never return 404 when called from allowed origin.
    """
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization, Content-Type",
    }
    response = client.options("/v1/dashboard/summary", headers=headers)
    
    # Must NEVER be 404 Not Found or 401 Unauthorized
    assert response.status_code != 404, "OPTIONS /v1/dashboard/summary returned 404!"
    assert response.status_code != 401, "OPTIONS /v1/dashboard/summary required authentication!"
    assert response.status_code in [200, 204]

    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"
    
    allowed_methods = response.headers.get("access-control-allow-methods", "")
    assert "GET" in allowed_methods or "*" in allowed_methods


def test_req_6f_dashboard_with_valid_api_key_returns_200(client, test_credentials):
    """F. GET /v1/dashboard/summary with valid API key returns 200."""
    key_alpha, _, _, _ = test_credentials
    headers = {"Authorization": f"Bearer {key_alpha}"}
    response = client.get("/v1/dashboard/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "tenant_cors_alpha"
    assert "requests_today" in data
    assert "allowed_requests" in data
    assert "blocked_requests" in data


def test_req_6g_dashboard_data_remains_tenant_scoped(client, test_credentials):
    """G. Dashboard summary data remains tenant-scoped."""
    key_alpha, _, key_beta, _ = test_credentials
    
    resp_alpha = client.get("/v1/dashboard/summary", headers={"Authorization": f"Bearer {key_alpha}"})
    resp_beta = client.get("/v1/dashboard/summary", headers={"Authorization": f"Bearer {key_beta}"})

    assert resp_alpha.status_code == 200
    assert resp_beta.status_code == 200

    data_alpha = resp_alpha.json()
    data_beta = resp_beta.json()

    assert data_alpha["tenant_id"] == "tenant_cors_alpha"
    assert data_beta["tenant_id"] == "tenant_cors_beta"
    assert data_alpha["tenant_id"] != data_beta["tenant_id"]


def test_req_6h_client_cannot_override_tenant_id(client, test_credentials):
    """H. A client cannot override tenant_id via query parameter or header."""
    key_alpha, _, _, _ = test_credentials
    headers = {
        "Authorization": f"Bearer {key_alpha}",
        "X-Tenant-ID": "tenant_cors_beta",
        "Tenant-ID": "tenant_cors_beta",
    }
    response = client.get("/v1/dashboard/summary?tenant_id=tenant_cors_beta", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "tenant_cors_alpha", "Client successfully forged tenant_id!"


def test_req_6i_unauthorized_origin_denied_cors_access(client):
    """I. Unknown/unauthorized origins do not receive permissive CORS access."""
    headers = {
        "Origin": "http://unauthorized-malicious-domain.com",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization",
    }
    response = client.options("/v1/dashboard/summary", headers=headers)
    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin != "http://unauthorized-malicious-domain.com"
    assert allow_origin != "*"


@pytest.mark.parametrize("path,method", [
    ("/health", "GET"),
    ("/ready", "GET"),
    ("/v1/requests", "POST"),
    ("/v1/executions", "POST"),
    ("/v1/approvals", "GET"),
    ("/v1/audit/events", "GET"),
    ("/v1/security/events", "GET"),
    ("/v1/dashboard/summary", "GET"),
    ("/v1/credentials", "POST"),
])
def test_req_8_audit_all_endpoints_preflight_compatibility(client, path, method):
    """8. Audit all existing endpoints for CORS preflight compatibility."""
    headers = {
        "Origin": "http://127.0.0.1:3000",
        "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": "Authorization, Content-Type",
    }
    response = client.options(path, headers=headers)
    assert response.status_code in [200, 204], f"Preflight OPTIONS {path} returned status {response.status_code}"
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:3000"
