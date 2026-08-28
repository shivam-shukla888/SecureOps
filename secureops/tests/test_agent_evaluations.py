import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
API_KEY_HEADER = {"Authorization": "Bearer test-secret-api-key-12345"}


def test_agent_security_evaluation_lifecycle_and_scenarios():
    # 1. Register Agent with authorized tools
    reg_payload = {
        "name": "SecOps Evaluated Agent",
        "provider": "custom",
        "framework": "langchain",
        "description": "Agent under automated security evaluation",
        "allowed_tools": ["knowledge_search", "ticket_lookup", "read_data", "delete_data"],
        "risk_level": "LOW"
    }

    res = client.post("/v1/agents", json=reg_payload, headers=API_KEY_HEADER)
    assert res.status_code == 201, f"Register agent failed: {res.text}"
    agent_id = res.json()["agent_id"]

    # 2. Trigger Security Evaluation Run (security-baseline)
    eval_req = {"test_suite": "security-baseline"}
    res = client.post(f"/v1/agents/{agent_id}/evaluations", json=eval_req, headers=API_KEY_HEADER)
    assert res.status_code == 201, f"Trigger evaluation failed: {res.text}"

    eval_data = res.json()
    assert eval_data["agent_id"] == agent_id
    assert eval_data["status"] == "COMPLETED"
    assert eval_data["total_tests"] > 0
    assert eval_data["passed"] > 0
    assert "risk_score" in eval_data
    assert "risk_level" in eval_data
    assert len(eval_data["findings"]) == eval_data["total_tests"]

    eval_id = eval_data["evaluation_id"]

    # Check specific finding statuses
    findings_by_id = {f["test_id"]: f for f in eval_data["findings"]}
    assert "PI-001" in findings_by_id  # Prompt Injection
    assert "JB-001" in findings_by_id  # Jailbreak
    assert "SSRF-001" in findings_by_id  # SSRF
    assert "TA-001" in findings_by_id  # Tool Abuse (Destructive Operation -> REQUIRE_APPROVAL)

    # 3. List Evaluations for Agent
    res = client.get(f"/v1/agents/{agent_id}/evaluations", headers=API_KEY_HEADER)
    assert res.status_code == 200
    evals = res.json()
    assert len(evals) >= 1
    assert any(e["evaluation_id"] == eval_id for e in evals)

    # 4. Get Specific Evaluation Detail
    res = client.get(f"/v1/agents/{agent_id}/evaluations/{eval_id}", headers=API_KEY_HEADER)
    assert res.status_code == 200
    assert res.json()["evaluation_id"] == eval_id

    # 5. Clean up Agent
    client.delete(f"/v1/agents/{agent_id}", headers=API_KEY_HEADER)
