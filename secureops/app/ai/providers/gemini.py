import asyncio
import logging
from typing import Optional, List
import httpx

from app.config import settings, DANGEROUS_DUMMY_KEYS
from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum
from app.ai.providers.base import BaseAIProvider, parse_and_validate_classifier_json
from app.ai.prompts import SYSTEM_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)

# Valid production Gemini models in priority fallback order
GEMINI_CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro-latest",
    "gemini-1.5-pro",
    "gemini-pro",
]

_DISCOVERED_GEMINI_MODELS: List[str] = []


def _normalize_gemini_model(raw_model: Optional[str]) -> str:
    if not raw_model:
        return "gemini-2.0-flash"
    cleaned = raw_model.strip("\"' \t\r\n")
    if cleaned.startswith("models/"):
        cleaned = cleaned[7:]
    if cleaned in GEMINI_CANDIDATE_MODELS:
        return cleaned
    if "2.5" in cleaned:
        return "gemini-2.5-flash"
    if "2.0" in cleaned or "2-flash" in cleaned:
        return "gemini-2.0-flash"
    if "pro" in cleaned.lower():
        return "gemini-1.5-pro"
    return "gemini-2.0-flash"


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

    async def _discover_models(self) -> List[str]:
        global _DISCOVERED_GEMINI_MODELS
        if _DISCOVERED_GEMINI_MODELS:
            return _DISCOVERED_GEMINI_MODELS

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    models_data = res.json().get("models", [])
                    discovered = [
                        m["name"].replace("models/", "")
                        for m in models_data
                        if "generateContent" in m.get("supportedGenerationMethods", [])
                    ]
                    if discovered:
                        _DISCOVERED_GEMINI_MODELS = discovered
                        return discovered
        except Exception as exc:
            logger.debug(f"Gemini model discovery skipped: {exc}")
        return []

    async def classify_request(self, user_request: str) -> ClassifierResult:
        if not self.is_configured:
            raise ValueError("GEMINI_API_KEY is not configured.")

        # Build candidate list with configured model first
        models_to_try: List[str] = [self.model]
        for m in GEMINI_CANDIDATE_MODELS:
            if m not in models_to_try:
                models_to_try.append(m)

        last_error = None
        for candidate_model in models_to_try:
            # 1. Attempt direct async HTTP REST API call
            try:
                return await self._classify_via_http(user_request, candidate_model)
            except Exception as http_err:
                last_error = http_err
                logger.info(f"Gemini HTTP REST call on {candidate_model} returned: {http_err}; checking SDK...")

            # 2. Fallback to google-genai SDK if installed
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=self.api_key)
                prompt = f"User Request: {user_request}"

                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=candidate_model,
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
                last_error = sdk_err
                logger.info(f"Gemini SDK call on {candidate_model} failed: {type(sdk_err).__name__}")

        # 3. Dynamic model discovery on 404
        if "404" in str(last_error) or "NOT_FOUND" in str(last_error):
            discovered = await self._discover_models()
            for disc_model in discovered:
                if disc_model not in models_to_try:
                    try:
                        return await self._classify_via_http(user_request, disc_model)
                    except Exception as disc_err:
                        last_error = disc_err

        if last_error:
            raise last_error
        raise RuntimeError("Gemini classification failed across all candidate models.")

    async def _classify_via_http(self, user_request: str, model_name: str) -> ClassifierResult:
        # Try v1beta then v1 endpoint URLs
        urls = [
            f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}",
            f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={self.api_key}",
        ]
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

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

        last_resp_err = None
        for url in urls:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code != 200:
                        err_detail = ""
                        try:
                            err_detail = response.json().get("error", {}).get("message", "")
                        except Exception:
                            pass
                        last_resp_err = f"Gemini API returned HTTP_{response.status_code}: {err_detail}"
                        continue

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

        if last_resp_err:
            raise RuntimeError(last_resp_err)
        raise RuntimeError("Gemini HTTP REST call failed on all endpoints.")
