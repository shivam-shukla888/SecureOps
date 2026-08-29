import logging
from typing import Optional, List
import httpx

from app.config import settings, DANGEROUS_DUMMY_KEYS
from app.schemas.decision import ClassifierResult
from app.ai.providers.base import BaseAIProvider, parse_and_validate_classifier_json
from app.ai.prompts import SYSTEM_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)

# Valid production Groq models in priority fallback order
GROQ_CANDIDATE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
]


def _normalize_groq_model(raw_model: Optional[str]) -> str:
    if not raw_model:
        return "llama-3.3-70b-versatile"
    cleaned = raw_model.strip("\"' \t\r\n")
    if cleaned in GROQ_CANDIDATE_MODELS:
        return cleaned
    if "8b" in cleaned.lower():
        return "llama-3.1-8b-instant"
    if "gpt-oss" in cleaned.lower() or "openai" in cleaned.lower():
        return "openai/gpt-oss-20b"
    if "mixtral" in cleaned.lower():
        return "mixtral-8x7b-32768"
    return "llama-3.3-70b-versatile"


class GroqProvider(BaseAIProvider):
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
        raw = self._explicit_api_key if self._explicit_api_key is not None else settings.GROQ_API_KEY
        return raw.strip("\"' \t\r\n") if raw else ""

    @property
    def model(self) -> str:
        raw = self._explicit_model if self._explicit_model is not None else settings.GROQ_MODEL
        return _normalize_groq_model(raw)

    @property
    def name(self) -> str:
        return "groq"

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key not in DANGEROUS_DUMMY_KEYS)

    async def classify_request(self, user_request: str) -> ClassifierResult:
        if not self.is_configured:
            raise ValueError("GROQ_API_KEY is not configured.")

        # Build candidate list with configured model first
        models_to_try: List[str] = [self.model]
        for m in GROQ_CANDIDATE_MODELS:
            if m not in models_to_try:
                models_to_try.append(m)

        last_error = None
        for candidate_model in models_to_try:
            # 1. Try using groq SDK if installed
            try:
                from groq import AsyncGroq

                client = AsyncGroq(api_key=self.api_key, timeout=self.timeout)
                response = await client.chat.completions.create(
                    model=candidate_model,
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
                pass
            except Exception as err:
                last_error = err
                logger.info(f"Groq SDK call on {candidate_model} returned: {type(err).__name__}; checking HTTP REST...")

            # 2. Fallback to direct HTTP REST API
            try:
                return await self._classify_via_http(user_request, candidate_model)
            except Exception as http_err:
                last_error = http_err
                logger.info(f"Groq HTTP REST call on {candidate_model} returned: {http_err}")

        if last_error:
            raise last_error
        raise RuntimeError("Groq classification failed across all candidate models.")

    async def _classify_via_http(self, user_request: str, model_name: str) -> ClassifierResult:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_name,
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
                
                # If json_object mode fails on older models, retry without response_format
                if response.status_code != 200:
                    payload.pop("response_format", None)
                    response = await client.post(url, json=payload, headers=headers)

                if response.status_code != 200:
                    err_detail = ""
                    try:
                        err_detail = response.json().get("error", {}).get("message", "")
                    except Exception:
                        pass
                    raise RuntimeError(
                        f"Groq API returned HTTP_{response.status_code}: {err_detail}"
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
