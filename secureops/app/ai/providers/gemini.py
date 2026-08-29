import asyncio
import logging
from typing import Optional
import httpx

from app.config import settings
from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum
from app.ai.providers.base import BaseAIProvider, parse_and_validate_classifier_json
from app.ai.prompts import SYSTEM_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)

# Standard Gemini safety settings to ensure security-evaluation prompts are not blocked
GEMINI_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Supported Gemini model aliases for graceful fallback if invalid model is supplied in environment
VALID_GEMINI_MODELS = {
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-1.0-pro",
}


class GeminiProvider(BaseAIProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 10.0,
    ):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        raw_model = model if model is not None else settings.GEMINI_MODEL
        # Normalize non-existent/outdated model names (e.g. gemini-3.5-flash)
        if raw_model and raw_model not in VALID_GEMINI_MODELS and "3.5" in raw_model:
            self.model = "gemini-1.5-flash"
        else:
            self.model = raw_model or "gemini-1.5-flash"
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def classify_request(self, user_request: str) -> ClassifierResult:
        if not self.is_configured:
            raise ValueError("GEMINI_API_KEY is not configured.")

        # Attempt direct HTTP REST classification first (non-blocking async with safety settings)
        try:
            return await self._classify_via_http(user_request)
        except Exception as http_err:
            logger.info(f"Gemini direct HTTP classification returned: {type(http_err).__name__}; checking SDK fallback...")

        # Fallback to google-genai SDK if available
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            prompt = f"User Request: {user_request}"
            
            # Execute SDK generate_content in thread pool to prevent event loop blocking
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
            logger.warning(f"Gemini SDK fallback also failed: {type(sdk_err).__name__}")
            raise sdk_err

        raise RuntimeError("Gemini classification failed via both HTTP REST and SDK.")

    async def _classify_via_http(self, user_request: str) -> ClassifierResult:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"User Request:\n{user_request}"}
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [
                    {"text": SYSTEM_CLASSIFICATION_PROMPT}
                ]
            },
            "safetySettings": GEMINI_SAFETY_SETTINGS,
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise RuntimeError(
                        f"Gemini API returned HTTP status {response.status_code}"
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
