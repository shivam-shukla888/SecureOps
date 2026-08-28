import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
API_KEY_HEADER = {"Authorization": "Bearer test-secret-api-key-12345"}


def test_adaptive_benchmark_execution_and_remediations():
    """
    [SIMULATED TEST] Validates adaptive benchmark execution loop, safety boundaries, and remediation generation.
    """
    # 1. Register test agent
    reg_payload = {
        "name": "Adaptive Benchmark Test Agent",
        "provider": "custom",
        "framework": "crewai",
        "description": "Agent under adaptive testing",
        "allowed_tools": ["knowledge_search", "read_data"],
        "risk_level": "LOW"
    }

    res = client.post("/v1/agents", json=reg_payload, headers=API_KEY_HEADER)
    assert res.status_code == 201
    agent_id = res.json()["agent_id"]

    # 2. Trigger Adaptive Benchmark
    bm_payload = {
        "benchmark": "security-baseline-v1",
        "adaptive": True
    }
    res = client.post(f"/v1/agents/{agent_id}/benchmarks", json=bm_payload, headers=API_KEY_HEADER)
    assert res.status_code == 201

    data = res.json()
    assert data["agent_id"] == agent_id
    assert "adaptive" in data["benchmark_name"]
    assert data["status"] == "COMPLETED"
    assert data["total_tests"] >= 20  # Base scenarios + adaptive variants

    # Verify every finding has actionable remediation and structured evidence
    for f in data["findings"]:
        assert "remediation" in f
        assert len(f["remediation"]) > 10
        assert "evidence" in f
        ev = f["evidence"]
        assert "benchmark_id" in ev
        assert "attack_id" in ev
        assert "policy_decision" in ev
        assert "timestamp" in ev

    # 3. Clean up
    client.delete(f"/v1/agents/{agent_id}", headers=API_KEY_HEADER)
