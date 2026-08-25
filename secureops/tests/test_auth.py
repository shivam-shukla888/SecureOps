def test_missing_auth_header_returns_401(client):
    response = client.post("/v1/requests", json={"user_id": "u123", "request": "search docs"})
    assert response.status_code == 401
    assert "Missing Authorization header" in response.json()["error"]["message"]


def test_invalid_api_key_returns_401(client):
    headers = {"Authorization": "Bearer invalid-wrong-key-999"}
    response = client.post("/v1/requests", json={"user_id": "u123", "request": "search docs"}, headers=headers)
    assert response.status_code == 401
    assert "Invalid or unauthorized API key" in response.json()["error"]["message"]
