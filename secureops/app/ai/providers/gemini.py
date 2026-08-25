import json
import logging
from typing import Optional
import httpx

from app.config import settings
from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum
from app.ai.providers.base import BaseAIProvider
from app.ai.prompts import SYSTEM_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

    async def classify_request(self, user_request: str) -> ClassifierResult:
        if not self.api_key:
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
                    response_schema=ClassifierResult,
                    temperature=0.0,
                ),
            )
            
            if response.text:
                data = json.loads(response.text)
                return ClassifierResult(**data)
        except ImportError:
            logger.info("google-genai SDK not found; using direct HTTP REST API for Gemini.")
        except Exception as err:
            logger.warning(f"SDK classification failed: {err}; falling back to HTTP REST call.")

        # Fallback to direct HTTP REST API call to Gemini
        return await self._classify_via_http(user_request)

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
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Gemini API returned HTTP {response.status_code}: {response.text}"
                )

            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned from Gemini API.")

            text_content = candidates[0]["content"]["parts"][0]["text"]
            
            # Clean markdown code blocks if model included them
            text_content = text_content.strip()
            if text_content.startswith("```json"):
                text_content = text_content[7:]
            if text_content.startswith("```"):
                text_content = text_content[3:]
            if text_content.endswith("```"):
                text_content = text_content[:-3]
            text_content = text_content.strip()

            parsed = json.loads(text_content)
            
            # Validate IntentEnum and RiskEnum
            intent_val = parsed.get("intent", "UNKNOWN").upper()
            try:
                intent_enum = IntentEnum(intent_val)
            except ValueError:
                intent_enum = IntentEnum.UNKNOWN

            risk_val = parsed.get("risk", "HIGH").upper()
            try:
                risk_enum = RiskEnum(risk_val)
            except ValueError:
                risk_enum = RiskEnum.HIGH

            return ClassifierResult(
                intent=intent_enum,
                resource=str(parsed.get("resource", "unknown")),
                risk=risk_enum,
                requires_approval=bool(parsed.get("requires_approval", True)),
            )
