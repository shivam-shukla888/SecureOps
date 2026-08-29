import asyncio
import logging
from typing import Optional
import httpx

from app.config import settings, DANGEROUS_DUMMY_KEYS
from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum
from app.ai.providers.base import BaseAIProvider, parse_and_validate_classifier_json
from app.ai.prompts import SYSTEM_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)

# Valid production Gemini models
VALID_GEMINI_MODELS = {
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
}


def _normalize_gemini_model(raw_model: Optional[str]) -> str:
    if not raw_model:
        return "gemini-1.5-flash"
    cleaned = raw_model.strip("\"' \t\r\n")
    if cleaned.startswith("models/"):
        cleaned = cleaned[7:]
    if cleaned in VALID_GEMINI_MODELS:
        return cleaned
    if "2.0" in cleaned or "2-flash" in cleaned:
        return "gemini-2.0-flash"
    if "pro" in cleaned.lower():
        return "gemini-1.5-pro"
    return "gemini-1.5-flash"


class GeminiProvider(BaseAIProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 15.0,
    ):
        self._explicit_api_key = api_key
        self._explicit_model = model
        self.timeout = timeout

    @property
    def api_key(self) -> str:
        raw = self._explicit_api_key if self._explicit_api_key is not None else settings.GEMINI_API_KEY
        return raw.strip("\"' \t\r\n") if raw else ""

    @property
    def model(self) -> str:
        raw = self._explicit_model if self._explicit_model is not None else settings.GEMINI_MODEL
        return _normalize_gemini_model(raw)

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key not in DANGEROUS_DUMMY_KEYS)

    async def classify_request(self, user_request: str) -> ClassifierResult:
        if not self.is_configured:
            raise ValueError("GEMINI_API_KEY is not configured.")

        # 1. Attempt direct async HTTP REST API call (fastest & most reliable)
        try:
            return await self._classify_via_http(user_request)
        except Exception as http_err:
            logger.info(f"Gemini HTTP REST call failed: {type(http_err).__name__}; attempting SDK fallback...")

        # 2. Fallback to google-genai SDK if installed
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            prompt = f"User Request: {user_request}"

            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_CLASSIFICATION_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
            )

            if response and response.text:
                return parse_and_validate_classifier_json(response.text, provider_name="Gemini")
        except ImportError:
            pass
        except Exception as sdk_err:
            logger.warning(f"Gemini SDK fallback failed: {type(sdk_err).__name__}")
            raise sdk_err

        raise RuntimeError("Gemini classification failed via both HTTP REST and SDK.")

    async def _classify_via_http(self, user_request: str) -> ClassifierResult:
        # Use query parameter key which is universally supported across Google API endpoints
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        # Single unified prompt payload compatible with all Gemini model versions
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{SYSTEM_CLASSIFICATION_PROMPT}\n\nUser Request:\n{user_request}"}
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code != 200:
                    raise RuntimeError(
                        f"Gemini API returned HTTP_{response.status_code}"
                    )

                res_json = response.json()

                # Check for prompt feedback blocks (e.g. SAFETY)
                prompt_feedback = res_json.get("promptFeedback", {})
                if prompt_feedback.get("blockReason") == "SAFETY":
                    logger.warning("Gemini prompt feedback flagged SAFETY block; classifying as UNKNOWN / HIGH risk.")
                    return ClassifierResult(
                        intent=IntentEnum.UNKNOWN,
                        resource=user_request,
                        risk=RiskEnum.HIGH,
                        requires_approval=True,
                    )

                candidates = res_json.get("candidates", [])
                if not candidates or not isinstance(candidates, list):
                    raise ValueError("No candidates returned from Gemini API.")

                candidate = candidates[0]
                finish_reason = candidate.get("finishReason")
                if finish_reason == "SAFETY":
                    logger.warning("Gemini candidate finishReason flagged SAFETY; classifying as UNKNOWN / HIGH risk.")
                    return ClassifierResult(
                        intent=IntentEnum.UNKNOWN,
                        resource=user_request,
                        risk=RiskEnum.HIGH,
                        requires_approval=True,
                    )

                text_content = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
                if not text_content:
                    raise ValueError("Gemini returned empty candidate content.")

                return parse_and_validate_classifier_json(text_content, provider_name="Gemini")
        except httpx.TimeoutException as te:
            raise RuntimeError(f"Gemini API timed out after {self.timeout}s: {te}")
        except httpx.RequestError as re:
            raise RuntimeError(f"Gemini API request failed: {re}")
