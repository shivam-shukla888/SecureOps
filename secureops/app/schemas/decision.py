from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class IntentEnum(str, Enum):
    SEARCH_DOCUMENT = "SEARCH_DOCUMENT"
    READ_DATA = "READ_DATA"
    SEND_DOCUMENT = "SEND_DOCUMENT"
    UPDATE_DATA = "UPDATE_DATA"
    DELETE_DATA = "DELETE_DATA"
    UNKNOWN = "UNKNOWN"


class RiskEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DecisionEnum(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    BLOCK = "BLOCK"


class ClassifierResult(BaseModel):
    intent: IntentEnum = IntentEnum.UNKNOWN
    resource: str = "unknown"
    risk: RiskEnum = RiskEnum.HIGH
    requires_approval: bool = True


class PolicyDecision(BaseModel):
    intent: IntentEnum
    resource: str
    ai_risk: RiskEnum
    policy_risk: RiskEnum
    requires_approval: bool
    decision: DecisionEnum
    override_applied: bool = False
    reason: str = ""


class SecurityGatewayResponse(BaseModel):
    request_id: str
    user_id: str
    intent: IntentEnum
    resource: str
    ai_risk: RiskEnum
    policy_risk: RiskEnum
    requires_approval: bool
    decision: DecisionEnum
    override_applied: bool
    provider_used: str = "gemini"
    fallback_used: bool = False
    approval_id: Optional[str] = None
    expires_at: Optional[str] = None
    execution_result: Dict[str, Any]
    timestamp: str
