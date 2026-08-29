import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict
from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum

logger = logging.getLogger(__name__)


def parse_and_validate_classifier_json(json_str: str, provider_name: str = "AI Provider") -> ClassifierResult:
    """
    Parses and validates raw JSON output from an AI provider according to strict gateway schemas.
    Rejects malformed JSON, invalid enums, missing required fields, and non-dict root payloads.
    Raises ValueError if validation fails.
    """
    if not json_str or not isinstance(json_str, str):
        raise ValueError(f"{provider_name} returned empty or invalid response string.")

    text_content = json_str.strip()
    if text_content.startswith("```json"):
        text_content = text_content[7:]
    if text_content.startswith("```"):
        text_content = text_content[3:]
    if text_content.endswith("```"):
        text_content = text_content[:-3]
    text_content = text_content.strip()

    try:
        parsed = json.loads(text_content)
    except Exception as exc:
        raise ValueError(f"{provider_name} returned malformed JSON: {exc}")

    if not isinstance(parsed, dict):
        raise ValueError(f"{provider_name} output must be a JSON object, got {type(parsed).__name__}.")

    # Required field: resource
    if "resource" not in parsed or parsed["resource"] is None:
        raise ValueError(f"{provider_name} output missing required field 'resource'.")
    resource_str = str(parsed["resource"]).strip()
    if not resource_str:
        raise ValueError(f"{provider_name} output field 'resource' cannot be empty.")

    # Required field: requires_approval
    if "requires_approval" not in parsed or parsed["requires_approval"] is None:
        raise ValueError(f"{provider_name} output missing required field 'requires_approval'.")
    raw_req_appr = parsed["requires_approval"]
    if isinstance(raw_req_appr, bool):
        requires_approval_val = raw_req_appr
    elif isinstance(raw_req_appr, str) and raw_req_appr.lower() in ("true", "false"):
        requires_approval_val = raw_req_appr.lower() == "true"
    else:
        raise ValueError(f"{provider_name} returned non-boolean 'requires_approval': {raw_req_appr}")

    # Required field: intent
    if "intent" not in parsed or parsed["intent"] is None:
        raise ValueError(f"{provider_name} output missing required field 'intent'.")
    intent_val = str(parsed["intent"]).strip().upper()
    try:
        intent_enum = IntentEnum(intent_val)
    except ValueError:
        raise ValueError(f"{provider_name} returned unknown or invalid intent: '{intent_val}'")

    # Required field: risk
    if "risk" not in parsed or parsed["risk"] is None:
        raise ValueError(f"{provider_name} output missing required field 'risk'.")
    risk_val = str(parsed["risk"]).strip().upper()
    try:
        risk_enum = RiskEnum(risk_val)
    except ValueError:
        raise ValueError(f"{provider_name} returned invalid risk value: '{risk_val}'")

    return ClassifierResult(
        intent=intent_enum,
        resource=resource_str,
        risk=risk_enum,
        requires_approval=requires_approval_val,
    )


class BaseAIProvider(ABC):
    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def is_configured(self) -> bool:
        return True

    @abstractmethod
    async def classify_request(self, user_request: str) -> ClassifierResult:
        """
        Classifies a user request into intent, resource, risk, and approval requirements.
        Must raise an Exception if classification fails.
        """
        pass
