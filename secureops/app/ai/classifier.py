import logging
from typing import Tuple, Optional

from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.groq import GroqProvider

logger = logging.getLogger(__name__)


class RequestClassifier:
    def __init__(
        self,
        primary_provider: Optional[BaseAIProvider] = None,
        fallback_provider: Optional[BaseAIProvider] = None,
    ):
        self.primary_provider = primary_provider or GeminiProvider()
        self.fallback_provider = fallback_provider or GroqProvider()

    async def classify(self, user_request: str) -> Tuple[ClassifierResult, bool, str, bool]:
        """
        Classifies the user request using the provider fallback chain (Gemini -> Groq).
        Returns a tuple of:
          (ClassifierResult, success_flag, provider_used, fallback_used)

        If both primary and fallback providers fail, fails closed returning
        (UNKNOWN / HIGH risk / requires_approval=True, False, "none", True).
        """
        # 1. Try Primary Provider (Gemini)
        try:
            result = await self.primary_provider.classify_request(user_request)
            return result, True, "gemini", False
        except Exception as exc_primary:
            logger.warning(
                f"Primary AI Provider (Gemini) failed: {exc_primary}. Triggering fallback provider (Groq)..."
            )

        # 2. Try Fallback Provider (Groq)
        try:
            result = await self.fallback_provider.classify_request(user_request)
            logger.info("Fallback AI Provider (Groq) successfully classified request.")
            return result, True, "groq", True
        except Exception as exc_fallback:
            logger.error(
                f"Fallback AI Provider (Groq) also failed: {exc_fallback}. All AI providers failed. Failing closed to UNKNOWN/HIGH risk."
            )

        # 3. Both Failed: Fail Closed
        fail_closed_result = ClassifierResult(
            intent=IntentEnum.UNKNOWN,
            resource="unknown",
            risk=RiskEnum.HIGH,
            requires_approval=True,
        )
        return fail_closed_result, False, "none", True
