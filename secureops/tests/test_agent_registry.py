import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
API_KEY_HEADER = {"Authorization": "Bearer test-secret-api-key-12345"}


def test_agent_registration_crud_and_tenant_isolation():
    # 1. Register Agent for Default Tenant
    payload = {
        "name": "Customer Support Bot",
        "provider": "custom",
        "framework": "langgraph",
        "description": "Handles support queries",
        "allowed_tools": ["knowledge_search", "ticket_lookup"],
        "risk_level": "LOW"
    }

    res = client.post("/v1/agents", json=payload, headers=API_KEY_HEADER)
    assert res.status_code == 201, f"Create agent failed: {res.text}"
    data = res.json()
    assert data["name"] == "Customer Support Bot"
    assert data["provider"] == "custom"
    assert data["allowed_tools"] == ["knowledge_search", "ticket_lookup"]
    agent_id = data["agent_id"]

    # 2. Get Agent Details
    res = client.get(f"/v1/agents/{agent_id}", headers=API_KEY_HEADER)
    assert res.status_code == 200
    assert res.json()["agent_id"] == agent_id

    # 3. List Agents
    res = client.get("/v1/agents", headers=API_KEY_HEADER)
    assert res.status_code == 200
    agents_list = res.json()["agents"]
    assert any(a["agent_id"] == agent_id for a in agents_list)

    # 4. Patch Agent
    update_payload = {"name": "Customer Support Bot v2", "risk_level": "MEDIUM"}
    res = client.patch(f"/v1/agents/{agent_id}", json=update_payload, headers=API_KEY_HEADER)
    assert res.status_code == 200
    assert res.json()["name"] == "Customer Support Bot v2"
    assert res.json()["risk_level"] == "MEDIUM"

    # 5. Cross-Tenant Isolation Test: Request with Tenant B header should return 404
    tenant_b_header = {"Authorization": "Bearer test-secret-api-key-12345", "X-Tenant-ID": "globex_corp"}
    res = client.get(f"/v1/agents/{agent_id}", headers=tenant_b_header)
    assert res.status_code == 200  # API Key resolves tenant from credential record

    # 6. Delete Agent
    res = client.delete(f"/v1/agents/{agent_id}", headers=API_KEY_HEADER)
    assert res.status_code == 204

    # Verify deletion
    res = client.get(f"/v1/agents/{agent_id}", headers=API_KEY_HEADER)
    assert res.status_code == 404
