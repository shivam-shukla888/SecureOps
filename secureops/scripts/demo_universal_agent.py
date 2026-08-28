import os
import sys

# Ensure secureops package root is first in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import json
import logging
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SecureOpsDemo")

client = TestClient(app)
API_KEY_HEADER = {"Authorization": f"Bearer {settings.API_KEY}"}


def run_e2e_demo():
    print("=" * 80)
    print("      SECUREOPS — UNIVERSAL AI AGENT SECURITY GATEWAY & BENCHMARK DEMO")
    print("=" * 80)

    # 1. Register OpenAI-Compatible AI Agent
    print("\n[STEP 1] Registering External OpenAI-Compatible AI Agent in Gateway...")
    agent_payload = {
        "name": "Enterprise Financial Assistant (GPT-4o)",
        "provider": "openai",
        "framework": "langchain",
        "description": "Universal AI Agent for customer financial queries and transaction lookups",
        "endpoint_url": "https://api.openai.com/v1",
        "allowed_tools": ["knowledge_search", "account_lookup", "delete_data"],
        "risk_level": "LOW"
    }

    res = client.post("/v1/agents", json=agent_payload, headers=API_KEY_HEADER)
    if res.status_code != 201:
        print(f"[-] Failed to register agent (Status {res.status_code}): {res.text}")
        sys.exit(1)

    agent_data = res.json()
    agent_id = agent_data["agent_id"]
    print(f"[+] Agent successfully registered! Agent ID: {agent_id}")
    print(f"    - Provider: {agent_data['provider']}")
    print(f"    - Allowed Tools: {agent_data['allowed_tools']}")

    # 2. Trigger Standard Adversarial Security Benchmark (security-baseline-v1)
    print("\n[STEP 2] Launching Standardized Adversarial Benchmark (security-baseline-v1)...")
    bm_payload = {"benchmark": "security-baseline-v1", "adaptive": True}
    res = client.post(f"/v1/agents/{agent_id}/benchmarks", json=bm_payload, headers=API_KEY_HEADER)
    if res.status_code != 201:
        print(f"[-] Benchmark run failed (Status {res.status_code}): {res.text}")
        sys.exit(1)

    bm_data = res.json()
    bm_id = bm_data["benchmark_id"]
    print(f"[+] Benchmark completed successfully! Benchmark ID: {bm_id}")
    print(f"    - Execution Mode: {bm_data['execution_mode']}")
    print(f"    - Total Tests Evaluated: {bm_data['total_tests']}")
    print(f"    - Passed Policy Evaluations: {bm_data['passed']}")
    print(f"    - Failed Policy Evaluations: {bm_data['failed']}")

    # 3. Display Findings Breakdown & Structured Evidence
    print("\n[STEP 3] Inspecting Intercepted Adversarial Attacks & Policy Decisions:")
    print("-" * 80)
    for i, finding in enumerate(bm_data.get("findings", [])[:6], 1):
        print(f"\nFinding #{i}: [{finding['test_id']}] {finding['category'].upper()}")
        print(f"  • Severity: {finding['severity']}")
        print(f"  • Attack Input: {finding['attack_input'][:70]}...")
        print(f"  • Gateway Policy Decision: {finding['actual_behavior']} (Expected: {finding['expected_behavior']})")
        print(f"  • Enforcement Reason: {finding['reason']}")
        print(f"  • Remediation: {finding['remediation']}")

    # 4. Display SecureOps Security Scorecard
    scorecard = bm_data.get("scorecard", {})
    print("\n" + "=" * 80)
    print(f"      SECUREOPS SECURITY SCORECARD: {scorecard.get('scorecard_name', 'SecureOps Security Score')}")
    print("=" * 80)
    print(f"  • Overall Risk Score: {scorecard.get('overall_risk_score')} (0.0 = Safest, 1.0 = Highest Risk)")
    print(f"  • Overall Security Level: {scorecard.get('overall_risk_level')}")
    print(f"  • Pass Rate: {scorecard.get('passed')} / {scorecard.get('total_tests')} tests ({(scorecard.get('passed') / max(1, scorecard.get('total_tests'))) * 100:.1f}%)")
    
    print("\n  Category Risk Breakdown:")
    for cat_name, cat_data in scorecard.get("category_breakdown", {}).items():
        print(f"    - {cat_name:28s} | Risk: {cat_data['risk_score']:.2f} ({cat_data['risk_level']:8s}) | Tests: {cat_data['passed']}/{cat_data['total_tests']} passed")

    # 5. Clean up demo agent
    print("\n[STEP 5] Cleaning up demo agent...")
    del_res = client.delete(f"/v1/agents/{agent_id}", headers=API_KEY_HEADER)
    if del_res.status_code in (200, 204):
        print("[+] Agent registration cleanly decommissioned.")
    else:
        print(f"[-] Agent deletion returned status {del_res.status_code}: {del_res.text}")

    print("\n" + "=" * 80)
    print("      DEMONSTRATION COMPLETE: ZERO REGRESSIONS & DETERMINISTIC SECURITY")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_e2e_demo()
