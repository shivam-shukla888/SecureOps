import logging
from typing import Optional
import httpx

from app.config import settings
from app.schemas.decision import ClassifierResult
from app.ai.providers.base import BaseAIProvider, parse_and_validate_classifier_json
from app.ai.prompts import SYSTEM_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 10.0,
    ):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model if model is not None else settings.GEMINI_MODEL
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def classify_request(self, user_request: str) -> ClassifierResult:
        if not self.is_configured:
            raise ValueError("GEMINI_API_KEY is not configured.")

        # Try using google-genai SDK if available
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            prompt = f"User Request: {user_request}"
            
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_CLASSIFICATION_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
            )
            
            if response.text:
                return parse_and_validate_classifier_json(response.text, provider_name="Gemini")
        except ImportError:
            logger.info("google-genai SDK not found; using direct HTTP REST API for Gemini.")
        except Exception as err:
            logger.warning(f"Gemini SDK call failed: {type(err).__name__}; falling back to HTTP REST call.")

        # Fallback to direct HTTP REST API call to Gemini
        return await self._classify_via_http(user_request)

    async def _classify_via_http(self, user_request: str) -> ClassifierResult:
        # Note: Avoid embedding API key in query parameters directly in error messages
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
                candidates = res_json.get("candidates", [])
                if not candidates or not isinstance(candidates, list):
                    raise ValueError("No candidates returned from Gemini API.")

                text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if not text_content:
                    raise ValueError("Gemini returned empty candidate content.")

                return parse_and_validate_classifier_json(text_content, provider_name="Gemini")
        except httpx.TimeoutException as te:
            raise RuntimeError(f"Gemini API timed out after {self.timeout}s: {te}")
        except httpx.RequestError as re:
            raise RuntimeError(f"Gemini API request failed: {re}")
