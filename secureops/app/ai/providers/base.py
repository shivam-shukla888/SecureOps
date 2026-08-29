import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum

logger = logging.getLogger(__name__)

# Intent synonyms mapping for robust normalization across varied LLM outputs
INTENT_SYNONYMS: Dict[str, IntentEnum] = {
    "SEARCH": IntentEnum.SEARCH_DOCUMENT,
    "SEARCH_DOCUMENT": IntentEnum.SEARCH_DOCUMENT,
    "SEARCH_DOCUMENTS": IntentEnum.SEARCH_DOCUMENT,
    "FIND_DOCUMENT": IntentEnum.SEARCH_DOCUMENT,
    "FIND_DOCUMENTS": IntentEnum.SEARCH_DOCUMENT,
    "READ": IntentEnum.READ_DATA,
    "READ_DATA": IntentEnum.READ_DATA,
    "GET_DATA": IntentEnum.READ_DATA,
    "RETRIEVE_DATA": IntentEnum.READ_DATA,
    "FETCH_DATA": IntentEnum.READ_DATA,
    "QUERY_DATA": IntentEnum.READ_DATA,
    "SEND": IntentEnum.SEND_DOCUMENT,
    "SEND_DOCUMENT": IntentEnum.SEND_DOCUMENT,
    "SEND_DOCUMENTS": IntentEnum.SEND_DOCUMENT,
    "TRANSMIT_DOCUMENT": IntentEnum.SEND_DOCUMENT,
    "SHARE_DOCUMENT": IntentEnum.SEND_DOCUMENT,
    "UPDATE": IntentEnum.UPDATE_DATA,
    "UPDATE_DATA": IntentEnum.UPDATE_DATA,
    "MODIFY_DATA": IntentEnum.UPDATE_DATA,
    "EDIT_DATA": IntentEnum.UPDATE_DATA,
    "DELETE": IntentEnum.DELETE_DATA,
    "DELETE_DATA": IntentEnum.DELETE_DATA,
    "PURGE_DATA": IntentEnum.DELETE_DATA,
    "DROP_DATA": IntentEnum.DELETE_DATA,
    "UNKNOWN": IntentEnum.UNKNOWN,
}


def parse_and_validate_classifier_json(json_str: str, provider_name: str = "AI Provider") -> ClassifierResult:
    """
    Parses and validates raw JSON output from an AI provider according to strict gateway schemas.
    Rejects malformed JSON, invalid enums, missing required fields, and non-dict root payloads.
    Raises ValueError if validation fails.
    """
    if not json_str or not isinstance(json_str, str):
        raise ValueError(f"{provider_name} returned empty or invalid response string.")

    text_content = json_str.strip()
    
    # Strip markdown formatting
    if text_content.startswith("```json"):
        text_content = text_content[7:]
    if text_content.startswith("```"):
        text_content = text_content[3:]
    if text_content.endswith("```"):
        text_content = text_content[:-3]
    text_content = text_content.strip()

    # If the response contains extra conversational text surrounding the JSON block, extract the JSON object
    if not (text_content.startswith("{") and text_content.endswith("}")):
        match = re.search(r"(\{.*\})", text_content, re.DOTALL)
        if match:
            text_content = match.group(1).strip()

    try:
        parsed = json.loads(text_content)
    except Exception as exc:
        raise ValueError(f"{provider_name} returned malformed JSON: {exc}")

    if not isinstance(parsed, dict):
        raise ValueError(f"{provider_name} output must be a JSON object, got {type(parsed).__name__}.")

    # 1. Validate & Normalize Resource
    if "resource" not in parsed or parsed["resource"] is None:
        raise ValueError(f"{provider_name} output missing required field 'resource'.")
    raw_resource = str(parsed["resource"]).strip()
    resource_str = raw_resource if raw_resource else "unknown"

    # 2. Validate & Normalize Requires Approval
    if "requires_approval" not in parsed or parsed["requires_approval"] is None:
        raise ValueError(f"{provider_name} output missing required field 'requires_approval'.")
    raw_req_appr = parsed["requires_approval"]
    if isinstance(raw_req_appr, bool):
        requires_approval_val = raw_req_appr
    elif isinstance(raw_req_appr, str) and raw_req_appr.lower() in ("true", "false"):
        requires_approval_val = raw_req_appr.lower() == "true"
    elif isinstance(raw_req_appr, (int, float)):
        requires_approval_val = bool(raw_req_appr)
    else:
        raise ValueError(f"{provider_name} returned non-boolean 'requires_approval': {raw_req_appr}")

    # 3. Validate & Normalize Intent
    if "intent" not in parsed or parsed["intent"] is None:
        raise ValueError(f"{provider_name} output missing required field 'intent'.")
    raw_intent = str(parsed["intent"]).strip().upper()
    
    if raw_intent in INTENT_SYNONYMS:
        intent_enum = INTENT_SYNONYMS[raw_intent]
    else:
        try:
            intent_enum = IntentEnum(raw_intent)
        except ValueError:
            raise ValueError(f"{provider_name} returned unknown or invalid intent: '{raw_intent}'")

    # 4. Validate & Normalize Risk
    if "risk" not in parsed or parsed["risk"] is None:
        raise ValueError(f"{provider_name} output missing required field 'risk'.")
    raw_risk = str(parsed["risk"]).strip().upper()
    try:
        risk_enum = RiskEnum(raw_risk)
    except ValueError:
        raise ValueError(f"{provider_name} returned invalid risk value: '{raw_risk}'")

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
    def model_name(self) -> str:
        return "default"

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
