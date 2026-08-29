import time
import logging
from typing import Tuple, Optional, List

from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.openai import PrimaryOpenAIProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.groq import GroqProvider

logger = logging.getLogger(__name__)


class _MockUnconfiguredProvider(BaseAIProvider):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_configured(self) -> bool:
        return False

    async def classify_request(self, user_request: str) -> ClassifierResult:
        raise ValueError(f"{self._name} is not configured.")


def _resolve_provider_identifier(provider: BaseAIProvider, slot: str) -> str:
    """Returns normalized provider name ('openai', 'gemini', 'groq', 'none')."""
    if hasattr(provider, "name") and provider.name in ("openai", "gemini", "groq", "none"):
        return provider.name
    return slot


class RequestClassifier:
    """
    Production AI Request Classifier implementing the explicit fallback hierarchy:
      1. Primary OpenAI-Compatible Provider (PRIMARY_API_KEY, PRIMARY_MODEL, PRIMARY_BASE_URL)
      2. Secondary Gemini Provider (GEMINI_API_KEY, GEMINI_MODEL)
      3. Tertiary Groq Provider (GROQ_API_KEY, GROQ_MODEL)
      4. Deterministic Fail-Closed Safety Fallback (UNKNOWN / HIGH risk / requires_approval=True)

    Fallback Semantics:
      - 'fallback_used' is False if the first available configured provider successfully classifies the request.
      - 'fallback_used' is True if a secondary/tertiary fallback was invoked due to a primary provider failure,
        or if all providers failed and the fail-closed fallback is active.
    """

    def __init__(
        self,
        openai_provider: Optional[BaseAIProvider] = None,
        gemini_provider: Optional[BaseAIProvider] = None,
        groq_provider: Optional[BaseAIProvider] = None,
        primary_provider: Optional[BaseAIProvider] = None,
        fallback_provider: Optional[BaseAIProvider] = None,
    ):
        if primary_provider is not None and openai_provider is None:
            self.openai_provider = primary_provider
        else:
            self.openai_provider = openai_provider or PrimaryOpenAIProvider()

        if fallback_provider is not None and groq_provider is None and gemini_provider is None and primary_provider is not None:
            # Legacy 2-provider test pattern: primary -> fallback
            self.gemini_provider = _MockUnconfiguredProvider("gemini")
            self.groq_provider = fallback_provider
        else:
            self.gemini_provider = gemini_provider or GeminiProvider()
            self.groq_provider = groq_provider or fallback_provider or GroqProvider()

    async def classify(self, user_request: str) -> Tuple[ClassifierResult, bool, str, bool]:
        """
        Classifies the user request through the explicit configured provider chain.
        Returns a tuple of:
          (ClassifierResult, success_flag, provider_used, fallback_used)
        """
        candidates: List[Tuple[BaseAIProvider, str]] = [
            (self.openai_provider, "openai"),
            (self.gemini_provider, "gemini"),
            (self.groq_provider, "groq"),
        ]

        configured_candidates: List[Tuple[BaseAIProvider, str]] = [
            (p, slot) for (p, slot) in candidates if p.is_configured
        ]

        if not configured_candidates:
            logger.warning(
                "[AI Classifier] No AI providers are configured. Failing closed to UNKNOWN/HIGH risk."
            )
            return (
                ClassifierResult(
                    intent=IntentEnum.UNKNOWN,
                    resource=user_request,
                    risk=RiskEnum.HIGH,
                    requires_approval=True,
                ),
                False,
                "none",
                True,
            )

        _, primary_slot = configured_candidates[0]

        for provider, slot in configured_candidates:
            start_time = time.time()
            provider_id = _resolve_provider_identifier(provider, slot)
            is_fallback = (slot != primary_slot)
            try:
                result = await provider.classify_request(user_request)
                if not isinstance(result, ClassifierResult):
                    raise ValueError(f"Returned invalid result type {type(result).__name__}")

                latency_ms = (time.time() - start_time) * 1000.0
                logger.info(
                    f"[AI Classifier] Provider: {provider_id} | Model: {getattr(provider, 'model_name', 'default')} | "
                    f"Latency: {latency_ms:.1f}ms | Fallback: {is_fallback} | Outcome: SUCCESS"
                )
                return result, True, provider_id, is_fallback

            except Exception as exc:
                latency_ms = (time.time() - start_time) * 1000.0
                failure_category = type(exc).__name__
                logger.warning(
                    f"[AI Classifier] Provider: {provider_id} | Model: {getattr(provider, 'model_name', 'default')} | "
                    f"Latency: {latency_ms:.1f}ms | Failure Category: {failure_category} | "
                    f"Outcome: FAILED -> Attempting next provider..."
                )

        # All configured providers failed -> Deterministic Fail-Closed Fallback
        logger.error(
            "[AI Classifier] All configured AI providers failed. Failing closed to UNKNOWN/HIGH risk."
        )
        return (
            ClassifierResult(
                intent=IntentEnum.UNKNOWN,
                resource=user_request,
                risk=RiskEnum.HIGH,
                requires_approval=True,
            ),
            False,
            "none",
            True,
        )

    async def classify_intent(self, user_request: str, user_id: str = "anonymous") -> ClassifierResult:
        res, success, provider, fallback = await self.classify(user_request)
        return res


intent_classifier = RequestClassifier()
