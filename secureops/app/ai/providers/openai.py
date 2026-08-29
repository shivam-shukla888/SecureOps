import logging
from typing import Optional
import httpx

from app.config import settings
from app.schemas.decision import ClassifierResult
from app.ai.providers.base import BaseAIProvider, parse_and_validate_classifier_json
from app.ai.prompts import SYSTEM_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


class PrimaryOpenAIProvider(BaseAIProvider):
    """
    Main Primary AI Provider configured with PRIMARY_API_KEY.
    Connects to OpenAI / OpenAI-compatible endpoint.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
    ):
        self.api_key = api_key if api_key is not None else settings.PRIMARY_API_KEY
        self.model = model if model is not None else (settings.PRIMARY_MODEL or "gpt-4o-mini")
        self.base_url = base_url if base_url is not None else (settings.PRIMARY_BASE_URL or "https://api.openai.com/v1")
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def classify_request(self, user_request: str) -> ClassifierResult:
        if not self.is_configured:
            raise ValueError("PRIMARY_API_KEY is not configured.")

        url = f"{self.base_url.rstrip('/')}/chat/completions"
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
                        f"Primary OpenAI API returned HTTP status {response.status_code}"
                    )

                res_json = response.json()
                choices = res_json.get("choices", [])
                if not choices or not isinstance(choices, list):
                    raise ValueError("Primary OpenAI returned no choices in response.")

                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    raise ValueError("Primary OpenAI returned empty content.")

                return parse_and_validate_classifier_json(content, provider_name="Primary OpenAI")
        except httpx.TimeoutException as te:
            raise RuntimeError(f"Primary OpenAI API timed out after {self.timeout}s: {te}")
        except httpx.RequestError as re:
            raise RuntimeError(f"Primary OpenAI API request failed: {re}")
