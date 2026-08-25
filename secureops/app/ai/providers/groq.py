import json
import logging
from typing import Optional
import httpx

from app.config import settings
from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum
from app.ai.providers.base import BaseAIProvider
from app.ai.prompts import SYSTEM_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


class GroqProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL

    async def classify_request(self, user_request: str) -> ClassifierResult:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        # Try using groq SDK if installed
        try:
            from groq import AsyncGroq

            client = AsyncGroq(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_CLASSIFICATION_PROMPT},
                    {"role": "user", "content": f"User Request:\n{user_request}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            content = response.choices[0].message.content
            if content:
                return self._parse_json_to_result(content)
        except ImportError:
            logger.info("groq SDK not found; using direct HTTP REST API for Groq.")
        except Exception as err:
            logger.warning(f"Groq SDK classification failed: {err}; falling back to HTTP REST API.")

        return await self._classify_via_http(user_request)

    async def _classify_via_http(self, user_request: str) -> ClassifierResult:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_CLASSIFICATION_PROMPT},
                {"role": "user", "content": f"User Request:\n{user_request}"},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Groq API returned HTTP {response.status_code}: {response.text}"
                )

            res_json = response.json()
            content = res_json["choices"][0]["message"]["content"]
            return self._parse_json_to_result(content)

    def _parse_json_to_result(self, json_str: str) -> ClassifierResult:
        text_content = json_str.strip()
        if text_content.startswith("```json"):
            text_content = text_content[7:]
        if text_content.startswith("```"):
            text_content = text_content[3:]
        if text_content.endswith("```"):
            text_content = text_content[:-3]
        text_content = text_content.strip()

        parsed = json.loads(text_content)

        # AI Output Validation Requirements:
        # Reject malformed JSON, missing resource, missing requires_approval, invalid risk/intent.
        if "resource" not in parsed or not parsed["resource"]:
            raise ValueError("Groq output missing required field 'resource'.")

        if "requires_approval" not in parsed:
            raise ValueError("Groq output missing required field 'requires_approval'.")

        intent_val = str(parsed.get("intent", "UNKNOWN")).upper()
        try:
            intent_enum = IntentEnum(intent_val)
        except ValueError:
            raise ValueError(f"Groq returned unknown or invalid intent: {intent_val}")

        risk_val = str(parsed.get("risk", "HIGH")).upper()
        try:
            risk_enum = RiskEnum(risk_val)
        except ValueError:
            raise ValueError(f"Groq returned invalid risk value: {risk_val}")

        return ClassifierResult(
            intent=intent_enum,
            resource=str(parsed["resource"]),
            risk=risk_enum,
            requires_approval=bool(parsed["requires_approval"]),
        )
