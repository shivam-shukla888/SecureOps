import pytest
from app.config import settings


def test_malformed_json_returns_400(client, auth_headers):
    response = client.post(
        "/v1/requests",
        content="this is not json",
        headers={**auth_headers, "Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert "Malformed request" in response.json()["error"]["message"]


def test_missing_required_user_id_returns_400(client, auth_headers):
    response = client.post(
        "/v1/requests",
        json={"request": "search docs"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "user_id" in response.json()["error"]["message"]


def test_missing_required_request_returns_400(client, auth_headers):
    response = client.post(
        "/v1/requests",
        json={"user_id": "u123"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "request" in response.json()["error"]["message"]


def test_forbidden_client_security_fields_rejected_with_400(client, auth_headers):
    """
    CRITICAL SECURITY TEST:
    Client trying to inject risk=LOW, intent=SEARCH_DOCUMENT, allowed=true must be rejected or ignored.
    """
    malicious_payload = {
        "user_id": "attacker_1",
        "request": "delete all databases",
        "risk": "LOW",
        "intent": "SEARCH_DOCUMENT",
        "allowed": True,
        "requires_approval": False,
    }
    response = client.post("/v1/requests", json=malicious_payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Forbidden client security parameters" in response.json()["error"]["message"]


def test_oversized_payload_returns_413(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "MAX_REQUEST_SIZE_BYTES", 100)
    large_payload = {"user_id": "u123", "request": "A" * 200}
    response = client.post("/v1/requests", json=large_payload, headers=auth_headers)
    assert response.status_code == 413
    assert "exceeds maximum allowed size" in response.json()["error"]["message"]
