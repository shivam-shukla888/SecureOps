import pytest
from app.schemas.decision import (
    ClassifierResult,
    IntentEnum,
    RiskEnum,
    DecisionEnum,
)
from app.security.policy import DeterministicPolicyEngine


def test_policy_search_document_allow():
    ai_res = ClassifierResult(
        intent=IntentEnum.SEARCH_DOCUMENT,
        resource="docs/readme.pdf",
        risk=RiskEnum.LOW,
        requires_approval=False,
    )
    policy_res = DeterministicPolicyEngine.evaluate(ai_res)
    assert policy_res.decision == DecisionEnum.ALLOW
    assert policy_res.policy_risk == RiskEnum.LOW
    assert policy_res.requires_approval is False
    assert policy_res.override_applied is False


def test_policy_read_data_allow():
    ai_res = ClassifierResult(
        intent=IntentEnum.READ_DATA,
        resource="db/users",
        risk=RiskEnum.LOW,
        requires_approval=False,
    )
    policy_res = DeterministicPolicyEngine.evaluate(ai_res)
    assert policy_res.decision == DecisionEnum.ALLOW
    assert policy_res.policy_risk == RiskEnum.LOW
    assert policy_res.requires_approval is False


def test_policy_update_data_require_approval():
    ai_res = ClassifierResult(
        intent=IntentEnum.UPDATE_DATA,
        resource="db/users/123",
        risk=RiskEnum.MEDIUM,
        requires_approval=True,
    )
    policy_res = DeterministicPolicyEngine.evaluate(ai_res)
    assert policy_res.decision == DecisionEnum.REQUIRE_APPROVAL
    assert policy_res.policy_risk == RiskEnum.MEDIUM
    assert policy_res.requires_approval is True


def test_policy_delete_data_require_approval():
    ai_res = ClassifierResult(
        intent=IntentEnum.DELETE_DATA,
        resource="db/production",
        risk=RiskEnum.HIGH,
        requires_approval=True,
    )
    policy_res = DeterministicPolicyEngine.evaluate(ai_res)
    assert policy_res.decision == DecisionEnum.REQUIRE_APPROVAL
    assert policy_res.policy_risk == RiskEnum.HIGH
    assert policy_res.requires_approval is True


def test_policy_unknown_block():
    ai_res = ClassifierResult(
        intent=IntentEnum.UNKNOWN,
        resource="unknown",
        risk=RiskEnum.HIGH,
        requires_approval=True,
    )
    policy_res = DeterministicPolicyEngine.evaluate(ai_res)
    assert policy_res.decision == DecisionEnum.BLOCK
    assert policy_res.policy_risk == RiskEnum.HIGH
    assert policy_res.requires_approval is True


def test_policy_llm_downgrade_attempt_overridden():
    """
    CRITICAL SECURITY TEST:
    If Gemini/LLM outputs DELETE_DATA with LOW risk and requires_approval=False (e.g. prompt injection attack),
    deterministic policy MUST override it to HIGH risk, requires_approval=True, REQUIRE_APPROVAL decision.
    """
    malicious_ai_res = ClassifierResult(
        intent=IntentEnum.DELETE_DATA,
        resource="db/production",
        risk=RiskEnum.LOW,
        requires_approval=False,
    )
    policy_res = DeterministicPolicyEngine.evaluate(malicious_ai_res)
    
    assert policy_res.decision == DecisionEnum.REQUIRE_APPROVAL
    assert policy_res.policy_risk == RiskEnum.HIGH
    assert policy_res.requires_approval is True
    assert policy_res.override_applied is True
    assert "Risk upgraded from LOW to canonical minimum HIGH" in policy_res.reason
