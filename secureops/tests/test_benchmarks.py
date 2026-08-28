import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
API_KEY_HEADER = {"Authorization": "Bearer test-secret-api-key-12345"}


def test_standard_security_benchmark_v1_execution_and_scorecard():
    # 1. Register OpenAI-Compatible Agent
    reg_payload = {
        "name": "Benchmark Tested OpenAI Agent",
        "provider": "openai",
        "framework": "langchain",
        "description": "Agent subjected to security-baseline-v1 benchmark",
        "allowed_tools": ["knowledge_search", "ticket_lookup", "read_data", "delete_data"],
        "risk_level": "LOW"
    }

    res = client.post("/v1/agents", json=reg_payload, headers=API_KEY_HEADER)
    assert res.status_code == 201, f"Register agent failed: {res.text}"
    agent_id = res.json()["agent_id"]

    # 2. Trigger Standard Security Benchmark (security-baseline-v1)
    bm_payload = {"benchmark": "security-baseline-v1"}
    res = client.post(f"/v1/agents/{agent_id}/benchmarks", json=bm_payload, headers=API_KEY_HEADER)
    assert res.status_code == 201, f"Run benchmark failed: {res.text}"

    data = res.json()
    assert data["agent_id"] == agent_id
    assert data["benchmark_name"] == "security-baseline-v1"
    assert data["execution_mode"] in ("MOCKED", "SIMULATED", "LIVE")
    assert data["status"] == "COMPLETED"
    assert data["total_tests"] > 0
    assert "scorecard" in data
    
    scorecard = data["scorecard"]
    assert scorecard["scorecard_name"] == "SecureOps Security Score"
    assert "overall_risk_score" in scorecard
    assert "overall_risk_level" in scorecard
    assert "category_breakdown" in scorecard

    # Verify category breakdown includes core categories
    breakdown = scorecard["category_breakdown"]
    assert "PROMPT_SECURITY" in breakdown
    assert "TOOL_SECURITY" in breakdown
    assert "DATA_SECURITY" in breakdown
    assert "NETWORK_SECURITY" in breakdown
    assert "FILESYSTEM_EXECUTION" in breakdown
    assert "AUTHORIZATION_RELIABILITY" in breakdown

    bm_id = data["benchmark_id"]

    # 3. List Benchmarks for Agent
    res = client.get(f"/v1/agents/{agent_id}/benchmarks", headers=API_KEY_HEADER)
    assert res.status_code == 200
    bms = res.json()
    assert len(bms) >= 1
    assert any(b["benchmark_id"] == bm_id for b in bms)

    # 4. Get Specific Benchmark Detail
    res = client.get(f"/v1/agents/{agent_id}/benchmarks/{bm_id}", headers=API_KEY_HEADER)
    assert res.status_code == 200
    assert res.json()["benchmark_id"] == bm_id

    # 5. Clean up Agent
    client.delete(f"/v1/agents/{agent_id}", headers=API_KEY_HEADER)
