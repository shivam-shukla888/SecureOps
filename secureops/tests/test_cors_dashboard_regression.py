import pytest
import asyncio
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


def test_1_health_check_returns_200(client):
    """1. Verify GET /health returns 200 and expected payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SecureOps API Gateway"
    assert "timestamp" in data


def test_2_readiness_check_returns_200(client):
    """2. Verify GET /ready returns expected readiness status."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ready", "degraded"]
    assert "rate_limiter" in data
    assert "database" in data
    assert "redis" in data


def test_3_dashboard_without_api_key_returns_401(client):
    """3. Verify GET /v1/dashboard/summary without API key returns 401."""
    response = client.get("/v1/dashboard/summary")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["status_code"] == 401


def test_4_dashboard_with_valid_api_key_returns_200(client, test_credentials):
    """4. Verify GET /v1/dashboard/summary with valid API key returns 200."""
    key_alpha, _, _, _ = test_credentials
    headers = {"Authorization": f"Bearer {key_alpha}"}
    response = client.get("/v1/dashboard/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "tenant_cors_alpha"
    assert "requests_today" in data
    assert "allowed_requests" in data
    assert "blocked_requests" in data
    assert "pending_approvals" in data


@pytest.mark.parametrize("origin", [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://secureops.vercel.app",
    "https://secureops-frontend.vercel.app",
    "https://secureops-preview-git-main-org.vercel.app",
    "https://secureops-gateway.onrender.com",
])
def test_5_6_7_9_browser_options_dashboard_cors_preflight_success(client, origin):
    """
    5. Browser-style OPTIONS /v1/dashboard/summary -> 200.
    6. CORS allow-origin is correct (exact match, not '*').
    7. CORS credentials are enabled (true).
    9. OPTIONS preflight does NOT require authentication.
    """
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization, content-type, idempotency-key",
    }
    response = client.options("/v1/dashboard/summary", headers=headers)
    
    # Must NEVER be 404 Not Found or 401 Unauthorized
    assert response.status_code != 404, f"OPTIONS /v1/dashboard/summary returned 404 from origin {origin}!"
    assert response.status_code != 401, f"OPTIONS /v1/dashboard/summary required authentication from origin {origin}!"
    assert response.status_code in [200, 204]

    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin == origin
    assert allow_origin != "*", "Wildcard '*' must never be used with credentials!"
    assert response.headers.get("access-control-allow-credentials") == "true"
    
    allowed_methods = response.headers.get("access-control-allow-methods", "")
    assert "GET" in allowed_methods or "*" in allowed_methods


def test_8_unauthorized_origin_denied_cors_access(client):
    """8. Unauthorized origin is rejected (no permissive allow-origin returned)."""
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
    ("/v1/agents", "GET"),
])
def test_10_all_endpoints_preflight_compatibility(client, path, method):
    """10. Audit all core endpoints for CORS preflight compatibility."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": "Authorization, Content-Type",
    }
    response = client.options(path, headers=headers)
    assert response.status_code in [200, 204], f"Preflight OPTIONS {path} returned {response.status_code}"
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


@pytest.mark.parametrize("path,method,payload", [
    ("/v1/requests", "POST", {"user_id": "u1", "request": "test"}),
    ("/v1/executions", "POST", {"request_id": "r1", "user_id": "u1", "tool_name": "lookup", "tool_input": {}}),
    ("/v1/approvals", "GET", None),
    ("/v1/audit/events", "GET", None),
    ("/v1/security/events", "GET", None),
    ("/v1/dashboard/summary", "GET", None),
    ("/v1/credentials", "POST", {"name": "test_key"}),
    ("/v1/agents", "GET", None),
])
def test_10b_protected_endpoints_retain_authentication(client, path, method, payload):
    """10b. Verify that all protected API endpoints strictly retain 401 without auth."""
    if method == "GET":
        resp = client.get(path)
    elif method == "POST":
        resp = client.post(path, json=payload or {})
    else:
        resp = client.request(method, path)
    assert resp.status_code in [401, 403], f"Endpoint {path} failed to require authentication! (returned {resp.status_code})"


def test_11_tenant_isolation_remains_intact(client, test_credentials):
    """11. Tenant isolation remains strictly intact across dashboard queries."""
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

    # Verify client cannot forge tenant_id
    forge_resp = client.get(
        "/v1/dashboard/summary?tenant_id=tenant_cors_beta",
        headers={"Authorization": f"Bearer {key_alpha}", "X-Tenant-ID": "tenant_cors_beta"}
    )
    assert forge_resp.status_code == 200
    assert forge_resp.json()["tenant_id"] == "tenant_cors_alpha"


def test_12_security_headers_middleware_intact(client):
    """12. Verify security headers are attached to responses."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "no-referrer"
