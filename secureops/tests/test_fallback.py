import asyncio
import pytest
from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum
from app.ai.classifier import RequestClassifier
from app.ai.providers.base import BaseAIProvider


class MockFailingProvider(BaseAIProvider):
    def __init__(self, error_msg: str = "Provider error"):
        self.error_msg = error_msg

    async def classify_request(self, user_request: str) -> ClassifierResult:
        raise RuntimeError(self.error_msg)


class MockSuccessProvider(BaseAIProvider):
    def __init__(self, intent: IntentEnum = IntentEnum.SEARCH_DOCUMENT):
        self.intent = intent

    async def classify_request(self, user_request: str) -> ClassifierResult:
        return ClassifierResult(
            intent=self.intent,
            resource="test_resource",
            risk=RiskEnum.LOW,
            requires_approval=False,
        )


def test_gemini_success_used():
    async def run_test():
        classifier = RequestClassifier(
            primary_provider=MockSuccessProvider(IntentEnum.SEARCH_DOCUMENT),
            fallback_provider=MockFailingProvider(),
        )
        return await classifier.classify("search docs")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is True
    assert provider == "gemini"
    assert fallback is False
    assert result.intent == IntentEnum.SEARCH_DOCUMENT


def test_gemini_timeout_triggers_groq_fallback():
    async def run_test():
        classifier = RequestClassifier(
            primary_provider=MockFailingProvider("Gemini API timeout"),
            fallback_provider=MockSuccessProvider(IntentEnum.READ_DATA),
        )
        return await classifier.classify("read data")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is True
    assert provider == "groq"
    assert fallback is True
    assert result.intent == IntentEnum.READ_DATA


def test_gemini_500_triggers_groq_fallback():
    async def run_test():
        classifier = RequestClassifier(
            primary_provider=MockFailingProvider("Gemini 500 Internal Server Error"),
            fallback_provider=MockSuccessProvider(IntentEnum.READ_DATA),
        )
        return await classifier.classify("read data")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is True
    assert provider == "groq"
    assert fallback is True


def test_gemini_malformed_output_triggers_groq_fallback():
    async def run_test():
        classifier = RequestClassifier(
            primary_provider=MockFailingProvider("Malformed JSON response"),
            fallback_provider=MockSuccessProvider(IntentEnum.SEARCH_DOCUMENT),
        )
        return await classifier.classify("search docs")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is True
    assert provider == "groq"
    assert fallback is True


def test_gemini_and_groq_both_fail_fails_closed():
    async def run_test():
        classifier = RequestClassifier(
            primary_provider=MockFailingProvider("Gemini down"),
            fallback_provider=MockFailingProvider("Groq down"),
        )
        return await classifier.classify("any prompt")

    result, success, provider, fallback = asyncio.run(run_test())

    assert success is False
    assert provider == "none"
    assert fallback is True
    assert result.intent == IntentEnum.UNKNOWN
    assert result.risk == RiskEnum.HIGH
    assert result.requires_approval is True
