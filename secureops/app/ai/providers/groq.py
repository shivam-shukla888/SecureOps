import logging
from typing import Optional
import httpx

from app.config import settings
from app.schemas.decision import ClassifierResult
from app.ai.providers.base import BaseAIProvider, parse_and_validate_classifier_json
from app.ai.prompts import SYSTEM_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


class GroqProvider(BaseAIProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 10.0,
    ):
        self.api_key = api_key if api_key is not None else settings.GROQ_API_KEY
        self.model = model if model is not None else settings.GROQ_MODEL
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "groq"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def classify_request(self, user_request: str) -> ClassifierResult:
        if not self.is_configured:
            raise ValueError("GROQ_API_KEY is not configured.")

        # Try using groq SDK if installed
        try:
            from groq import AsyncGroq

            client = AsyncGroq(api_key=self.api_key, timeout=self.timeout)
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
                return parse_and_validate_classifier_json(content, provider_name="Groq")
        except ImportError:
            logger.info("groq SDK not found; using direct HTTP REST API for Groq.")
        except Exception as err:
            logger.warning(f"Groq SDK classification call failed: {type(err).__name__}; falling back to HTTP REST API.")

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

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code != 200:
                    raise RuntimeError(
                        f"Groq API returned HTTP status {response.status_code}"
                    )

                res_json = response.json()
                choices = res_json.get("choices", [])
                if not choices or not isinstance(choices, list):
                    raise ValueError("Groq returned no choices in response.")

                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    raise ValueError("Groq returned empty content.")

                return parse_and_validate_classifier_json(content, provider_name="Groq")
        except httpx.TimeoutException as te:
            raise RuntimeError(f"Groq API timed out after {self.timeout}s: {te}")
        except httpx.RequestError as re:
            raise RuntimeError(f"Groq API request failed: {re}")
