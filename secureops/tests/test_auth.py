from unittest.mock import patch, AsyncMock
from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum


def test_missing_auth_header_returns_401(client):
    response = client.post("/v1/requests", json={"user_id": "u123", "request": "search docs"})
    assert response.status_code == 401
    assert "Missing Authorization header" in response.json()["error"]["message"]


def test_invalid_api_key_returns_401(client):
    headers = {"Authorization": "Bearer invalid-wrong-key-999"}
    response = client.post("/v1/requests", json={"user_id": "u123", "request": "search docs"}, headers=headers)
    assert response.status_code == 401
    assert "Invalid or unauthorized API key" in response.json()["error"]["message"]


def test_duplicate_bearer_prefix_sanitized_and_authenticated(client, auth_headers):
    # Tests that 'Bearer Bearer <key>' or quotes around token are sanitized correctly
    raw_key = auth_headers["Authorization"].split("Bearer ")[1]
    duplicate_header = {"Authorization": f"Bearer Bearer '{raw_key}'"}
    
    mock_res = ClassifierResult(intent=IntentEnum.SEARCH_DOCUMENT, resource="docs", risk=RiskEnum.LOW, requires_approval=False)
    with patch("app.ai.classifier.RequestClassifier.classify", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = (mock_res, True, "gemini", False)
        response = client.post("/v1/requests", json={"user_id": "u123", "request": "search docs"}, headers=duplicate_header)
        assert response.status_code == 200
        assert response.json()["decision"] == "ALLOW"


def test_openapi_security_scheme_defined(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "securitySchemes" in schema["components"]
    assert "HTTPBearer" in schema["components"]["securitySchemes"]
    assert schema["components"]["securitySchemes"]["HTTPBearer"]["type"] == "http"
    assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"


def test_valid_auth_with_malformed_json_body_returns_400(client, auth_headers):
    response = client.post(
        "/v1/requests",
        content="this is not valid json",
        headers={**auth_headers, "Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert "Malformed request" in response.json()["error"]["message"]
