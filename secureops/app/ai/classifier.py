import logging
from typing import Tuple, Optional

from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.openai import PrimaryOpenAIProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.groq import GroqProvider

logger = logging.getLogger(__name__)


class RequestClassifier:
    """
    Production AI Request Classifier implementing the explicit fallback hierarchy:
      1. Primary OpenAI-Compatible Provider (PRIMARY_API_KEY, PRIMARY_MODEL, PRIMARY_BASE_URL)
      2. Secondary Gemini Provider (GEMINI_API_KEY, GEMINI_MODEL)
      3. Tertiary Groq Provider (GROQ_API_KEY, GROQ_MODEL)
      4. Deterministic Fail-Closed Safety Fallback (UNKNOWN / HIGH risk / requires_approval=True)
    """

    def __init__(
        self,
        openai_provider: Optional[BaseAIProvider] = None,
        gemini_provider: Optional[BaseAIProvider] = None,
        groq_provider: Optional[BaseAIProvider] = None,
        primary_provider: Optional[BaseAIProvider] = None,
        fallback_provider: Optional[BaseAIProvider] = None,
    ):
        # Allow legacy parameter aliases for backwards compatibility in tests
        self.openai_provider = openai_provider or primary_provider or PrimaryOpenAIProvider()
        self.gemini_provider = gemini_provider or GeminiProvider()
        self.groq_provider = groq_provider or fallback_provider or GroqProvider()

    async def classify(self, user_request: str) -> Tuple[ClassifierResult, bool, str, bool]:
        """
        Classifies the user request through the explicit provider chain.
        Returns a tuple of:
          (ClassifierResult, success_flag, provider_used, fallback_used)

        Provider metadata contract:
          - Primary OpenAI succeeds : provider="openai", fallback=False, success=True
          - Gemini succeeds        : provider="gemini", fallback=True,  success=True
          - Groq succeeds          : provider="groq",   fallback=True,  success=True
          - All providers fail     : provider="none",   fallback=True,  success=False (Fail Closed)
        """
        # 1. Try Primary OpenAI Provider
        try:
            result = await self.openai_provider.classify_request(user_request)
            if not isinstance(result, ClassifierResult):
                raise ValueError(f"Primary OpenAI returned invalid result type {type(result).__name__}")
            return result, True, "openai", False
        except Exception as exc_openai:
            logger.warning(
                f"Primary AI Provider (OpenAI) unavailable or failed: {exc_openai}. Trying Gemini..."
            )

        # 2. Try Secondary Gemini Provider
        try:
            result = await self.gemini_provider.classify_request(user_request)
            if not isinstance(result, ClassifierResult):
                raise ValueError(f"Gemini returned invalid result type {type(result).__name__}")
            logger.info("Secondary AI Provider (Gemini) successfully classified request.")
            return result, True, "gemini", True
        except Exception as exc_gemini:
            logger.warning(
                f"Secondary AI Provider (Gemini) unavailable or failed: {exc_gemini}. Trying Groq..."
            )

        # 3. Try Tertiary Groq Provider
        try:
            result = await self.groq_provider.classify_request(user_request)
            if not isinstance(result, ClassifierResult):
                raise ValueError(f"Groq returned invalid result type {type(result).__name__}")
            logger.info("Tertiary AI Provider (Groq) successfully classified request.")
            return result, True, "groq", True
        except Exception as exc_groq:
            logger.error(
                f"Tertiary AI Provider (Groq) unavailable or failed: {exc_groq}. All AI providers failed. Failing closed to UNKNOWN/HIGH risk."
            )

        # 4. All Providers Failed -> Deterministic Fail-Closed Safety Fallback
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
