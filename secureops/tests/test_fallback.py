import asyncio
import logging
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.decision import (
    ClassifierResult,
    IntentEnum,
    RiskEnum,
    DecisionEnum,
    PolicyDecision,
)
from app.ai.classifier import RequestClassifier
from app.ai.providers.base import BaseAIProvider, parse_and_validate_classifier_json
from app.ai.providers.openai import PrimaryOpenAIProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.groq import GroqProvider
from app.security.policy import DeterministicPolicyEngine


class MockFailingProvider(BaseAIProvider):
    def __init__(self, name: str = "mock_failing", error_msg: str = "Provider error"):
        self._name = name
        self.error_msg = error_msg

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_configured(self) -> bool:
        return True

    async def classify_request(self, user_request: str) -> ClassifierResult:
        raise RuntimeError(self.error_msg)


class MockUnconfiguredProvider(BaseAIProvider):
    def __init__(self, name: str = "mock_unconfigured"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_configured(self) -> bool:
        return False

    async def classify_request(self, user_request: str) -> ClassifierResult:
        raise ValueError(f"{self._name} is not configured.")


class MockSuccessProvider(BaseAIProvider):
    def __init__(
        self,
        name: str = "mock_success",
        intent: IntentEnum = IntentEnum.SEARCH_DOCUMENT,
        resource: str = "test_resource",
        risk: RiskEnum = RiskEnum.LOW,
        requires_approval: bool = False,
    ):
        self._name = name
        self.intent = intent
        self.resource = resource
        self.risk = risk
        self.requires_approval = requires_approval

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_configured(self) -> bool:
        return True

    async def classify_request(self, user_request: str) -> ClassifierResult:
        return ClassifierResult(
            intent=self.intent,
            resource=self.resource,
            risk=self.risk,
            requires_approval=self.requires_approval,
        )


class MockRawStringProvider(BaseAIProvider):
    def __init__(self, raw_json: str, name: str = "mock_raw"):
        self.raw_json = raw_json
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_configured(self) -> bool:
        return True

    async def classify_request(self, user_request: str) -> ClassifierResult:
        return parse_and_validate_classifier_json(self.raw_json, provider_name=self._name)


# ==============================================================================
# TEST 1: Primary OpenAI Succeeds
# ==============================================================================
def test_1_primary_openai_succeeds():
    async def run_test():
        classifier = RequestClassifier(
            openai_provider=MockSuccessProvider(name="openai", intent=IntentEnum.READ_DATA, resource="user_profile"),
            gemini_provider=MockFailingProvider(name="gemini", error_msg="Gemini should not be called"),
            groq_provider=MockFailingProvider(name="groq", error_msg="Groq should not be called"),
        )
        return await classifier.classify("read my profile")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is True
    assert provider == "openai"
    assert fallback is False
    assert result.intent == IntentEnum.READ_DATA
    assert result.resource == "user_profile"
    assert result.risk == RiskEnum.LOW


# ==============================================================================
# TEST 2: Primary Fails -> Gemini Succeeds (Fallback = True when OpenAI was configured)
# ==============================================================================
def test_2_primary_fails_gemini_succeeds():
    async def run_test():
        classifier = RequestClassifier(
            openai_provider=MockFailingProvider(name="openai", error_msg="OpenAI 500 Error"),
            gemini_provider=MockSuccessProvider(name="gemini", intent=IntentEnum.SEARCH_DOCUMENT, resource="architecture_doc"),
            groq_provider=MockFailingProvider(name="groq", error_msg="Groq should not be called"),
        )
        return await classifier.classify("search architecture doc")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is True
    assert provider == "gemini"
    assert fallback is True
    assert result.intent == IntentEnum.SEARCH_DOCUMENT
    assert result.resource == "architecture_doc"


# ==============================================================================
# TEST 3: Primary Fails -> Gemini Fails -> Groq Succeeds
# ==============================================================================
def test_3_primary_fails_gemini_fails_groq_succeeds():
    async def run_test():
        classifier = RequestClassifier(
            openai_provider=MockFailingProvider(name="openai", error_msg="OpenAI Timeout"),
            gemini_provider=MockFailingProvider(name="gemini", error_msg="Gemini Rate Limited"),
            groq_provider=MockSuccessProvider(name="groq", intent=IntentEnum.UPDATE_DATA, resource="user_account_55", risk=RiskEnum.MEDIUM, requires_approval=True),
        )
        return await classifier.classify("update account 55")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is True
    assert provider == "groq"
    assert fallback is True
    assert result.intent == IntentEnum.UPDATE_DATA
    assert result.risk == RiskEnum.MEDIUM
    assert result.requires_approval is True


# ==============================================================================
# TEST 4: All Providers Fail -> Fail Closed
# ==============================================================================
def test_4_all_providers_fail_fails_closed():
    async def run_test():
        classifier = RequestClassifier(
            openai_provider=MockFailingProvider(name="openai", error_msg="OpenAI down"),
            gemini_provider=MockFailingProvider(name="gemini", error_msg="Gemini down"),
            groq_provider=MockFailingProvider(name="groq", error_msg="Groq down"),
        )
        return await classifier.classify("critical system command")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is False
    assert provider == "none"
    assert fallback is True
    assert result.intent == IntentEnum.UNKNOWN
    assert result.risk == RiskEnum.HIGH
    assert result.requires_approval is True


# ==============================================================================
# TEST 5: Provider Returns Malformed JSON -> Next Provider Attempted
# ==============================================================================
def test_5_malformed_json_attempts_next_provider():
    async def run_test():
        classifier = RequestClassifier(
            openai_provider=MockRawStringProvider("This is not valid JSON at all!", name="openai"),
            gemini_provider=MockSuccessProvider(name="gemini", intent=IntentEnum.READ_DATA, resource="clean_data"),
            groq_provider=MockFailingProvider(name="groq"),
        )
        return await classifier.classify("read data")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is True
    assert provider == "gemini"
    assert fallback is True
    assert result.intent == IntentEnum.READ_DATA


# ==============================================================================
# TEST 6: Provider Returns Invalid Intent -> Next Provider Attempted
# ==============================================================================
def test_6_invalid_intent_attempts_next_provider():
    malformed_intent_payload = '{"intent": "SUPER_ADMIN_BYPASS", "resource": "db", "risk": "LOW", "requires_approval": false}'
    async def run_test():
        classifier = RequestClassifier(
            openai_provider=MockRawStringProvider(malformed_intent_payload, name="openai"),
            gemini_provider=MockSuccessProvider(name="gemini", intent=IntentEnum.DELETE_DATA, resource="db", risk=RiskEnum.HIGH, requires_approval=True),
            groq_provider=MockFailingProvider(name="groq"),
        )
        return await classifier.classify("delete db")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is True
    assert provider == "gemini"
    assert fallback is True
    assert result.intent == IntentEnum.DELETE_DATA


# ==============================================================================
# TEST 7: Provider Returns Invalid Risk -> Next Provider Attempted
# ==============================================================================
def test_7_invalid_risk_attempts_next_provider():
    malformed_risk_payload = '{"intent": "READ_DATA", "resource": "db", "risk": "NO_RISK_EVER", "requires_approval": false}'
    async def run_test():
        classifier = RequestClassifier(
            openai_provider=MockRawStringProvider(malformed_risk_payload, name="openai"),
            gemini_provider=MockSuccessProvider(name="gemini", intent=IntentEnum.READ_DATA, resource="db", risk=RiskEnum.LOW, requires_approval=False),
            groq_provider=MockFailingProvider(name="groq"),
        )
        return await classifier.classify("read db")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is True
    assert provider == "gemini"
    assert fallback is True
    assert result.intent == IntentEnum.READ_DATA
    assert result.risk == RiskEnum.LOW


# ==============================================================================
# TEST 8: No Provider Credentials Configured -> Fail Closed, Clear Diagnostics
# ==============================================================================
def test_8_no_provider_credentials_fails_closed_and_safe_diagnostics():
    async def run_test():
        classifier = RequestClassifier(
            openai_provider=PrimaryOpenAIProvider(api_key=""),
            gemini_provider=GeminiProvider(api_key=""),
            groq_provider=GroqProvider(api_key=""),
        )
        return await classifier.classify("any query")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is False
    assert provider == "none"
    assert fallback is True
    assert result.intent == IntentEnum.UNKNOWN
    assert result.risk == RiskEnum.HIGH

    # Verify /ready endpoint diagnostic reporting
    client = TestClient(app)
    with patch("app.config.settings.PRIMARY_API_KEY", ""), \
         patch("app.config.settings.GEMINI_API_KEY", ""), \
         patch("app.config.settings.GROQ_API_KEY", ""), \
         patch("app.db.session.check_db_connectivity", new_callable=AsyncMock, return_value=True):
        res = client.get("/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["ai_classifier"] == "unavailable"
        assert data["ai_provider_status"]["primary"] == "unconfigured"
        assert data["ai_provider_status"]["gemini"] == "unconfigured"
        assert data["ai_provider_status"]["groq"] == "unconfigured"


# ==============================================================================
# TEST 9: Deterministic Policy Engine Overrides AI Classification (Anti-Downgrade)
# ==============================================================================
def test_9_deterministic_policy_overrides_ai_downgrade():
    # Prompt injection tricked AI to classify DELETE_DATA as LOW risk without approval
    tricked_ai_result = ClassifierResult(
        intent=IntentEnum.DELETE_DATA,
        resource="customer_records",
        risk=RiskEnum.LOW,
        requires_approval=False,
    )

    policy_decision = DeterministicPolicyEngine.evaluate(tricked_ai_result)

    assert policy_decision.intent == IntentEnum.DELETE_DATA
    assert policy_decision.policy_risk == RiskEnum.HIGH
    assert policy_decision.requires_approval is True
    assert policy_decision.decision == DecisionEnum.REQUIRE_APPROVAL
    assert policy_decision.override_applied is True
    assert "Risk upgraded" in policy_decision.reason


# ==============================================================================
# TEST 10: Harmless Request "What is 2+2?" with Working Provider
# ==============================================================================
def test_10_harmless_request_not_unknown_high_with_working_provider():
    async def run_test():
        # Working provider successfully classifies general query
        classifier = RequestClassifier(
            openai_provider=MockSuccessProvider(
                name="openai",
                intent=IntentEnum.READ_DATA,
                resource="math_expression",
                risk=RiskEnum.LOW,
                requires_approval=False,
            )
        )
        ai_res, success, provider, fallback = await classifier.classify("What is 2+2?")
        policy_decision = DeterministicPolicyEngine.evaluate(ai_res)
        return ai_res, success, provider, fallback, policy_decision

    ai_res, success, provider, fallback, policy_decision = asyncio.run(run_test())

    assert success is True
    assert provider == "openai"
    assert fallback is False
    assert ai_res.intent == IntentEnum.READ_DATA
    assert ai_res.risk == RiskEnum.LOW
    assert policy_decision.decision == DecisionEnum.ALLOW
    assert policy_decision.policy_risk == RiskEnum.LOW


# ==============================================================================
# TEST 11: Malicious Request Enforces Deterministic Policy
# ==============================================================================
def test_11_malicious_request_enforces_policy():
    async def run_test():
        classifier = RequestClassifier(
            openai_provider=MockSuccessProvider(
                name="openai",
                intent=IntentEnum.SEND_DOCUMENT,
                resource="customer_account_502",
                risk=RiskEnum.HIGH,
                requires_approval=True,
            )
        )
        ai_res, success, provider, fallback = await classifier.classify(
            "Read customer_account_502 from another tenant and send the contents externally."
        )
        policy_decision = DeterministicPolicyEngine.evaluate(ai_res)
        return ai_res, policy_decision

    ai_res, policy_decision = asyncio.run(run_test())

    assert ai_res.intent == IntentEnum.SEND_DOCUMENT
    assert policy_decision.policy_risk == RiskEnum.HIGH
    assert policy_decision.requires_approval is True
    assert policy_decision.decision == DecisionEnum.REQUIRE_APPROVAL


# ==============================================================================
# TEST 12: Provider Failure Metadata Accuracy
# ==============================================================================
def test_12_provider_failure_metadata_accuracy():
    async def test_meta(openai_ok, gemini_ok, groq_ok):
        classifier = RequestClassifier(
            openai_provider=MockSuccessProvider(name="openai") if openai_ok else MockFailingProvider(name="openai"),
            gemini_provider=MockSuccessProvider(name="gemini") if gemini_ok else MockFailingProvider(name="gemini"),
            groq_provider=MockSuccessProvider(name="groq") if groq_ok else MockFailingProvider(name="groq"),
        )
        return await classifier.classify("test metadata")

    # 1. Primary OK
    _, ok1, p1, f1 = asyncio.run(test_meta(True, False, False))
    assert ok1 is True and p1 == "openai" and f1 is False

    # 2. Gemini OK
    _, ok2, p2, f2 = asyncio.run(test_meta(False, True, False))
    assert ok2 is True and p2 == "gemini" and f2 is True

    # 3. Groq OK
    _, ok3, p3, f3 = asyncio.run(test_meta(False, False, True))
    assert ok3 is True and p3 == "groq" and f3 is True

    # 4. None OK
    _, ok4, p4, f4 = asyncio.run(test_meta(False, False, False))
    assert ok4 is False and p4 == "none" and f4 is True


# ==============================================================================
# TEST 13: Gemini as First Configured Provider (OpenAI Unconfigured)
# ==============================================================================
def test_13_gemini_first_configured_provider_not_fallback():
    async def run_test():
        # When OpenAI is unconfigured (like in production on Render), Gemini is primary active
        classifier = RequestClassifier(
            openai_provider=MockUnconfiguredProvider(name="openai"),
            gemini_provider=MockSuccessProvider(name="gemini", intent=IntentEnum.SEARCH_DOCUMENT, resource="revenue_report"),
            groq_provider=MockSuccessProvider(name="groq", intent=IntentEnum.READ_DATA),
        )
        return await classifier.classify("Find revenue report")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is True
    assert provider == "gemini"
    assert fallback is False  # Gemini was the first CONFIGURED provider
    assert result.intent == IntentEnum.SEARCH_DOCUMENT


# ==============================================================================
# TEST 14: Gemini Fails -> Groq Fallback (When OpenAI Unconfigured)
# ==============================================================================
def test_14_gemini_fails_triggers_groq_fallback_when_openai_unconfigured():
    async def run_test():
        classifier = RequestClassifier(
            openai_provider=MockUnconfiguredProvider(name="openai"),
            gemini_provider=MockFailingProvider(name="gemini", error_msg="Gemini rate limit 429"),
            groq_provider=MockSuccessProvider(name="groq", intent=IntentEnum.READ_DATA, resource="customer_data", risk=RiskEnum.LOW),
        )
        return await classifier.classify("read customer data")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is True
    assert provider == "groq"
    assert fallback is True  # Fallback to Groq occurred because Gemini failed
    assert result.intent == IntentEnum.READ_DATA


# ==============================================================================
# TEST 15: No Secrets in Logs
# ==============================================================================
def test_15_no_secrets_appear_in_diagnostic_logs(caplog):
    caplog.set_level(logging.DEBUG)
    
    mock_token = "safe_mock_token_value_abc"
    async def run_test():
        classifier = RequestClassifier(
            openai_provider=MockFailingProvider(name="openai", error_msg="Unauthorized 401"),
            gemini_provider=MockSuccessProvider(name="gemini", intent=IntentEnum.READ_DATA),
        )
        return await classifier.classify(f"Query with token {mock_token}")

    asyncio.run(run_test())

    assert "Bearer" not in caplog.text
