from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator

FORBIDDEN_CLIENT_FIELDS = {
    "intent",
    "risk",
    "requires_approval",
    "requiresApproval",
    "allowed",
    "security_decision",
    "securityDecision",
    "policy_risk",
    "validation",
    "tool",
    "handler",
    "function",
    "permission",
}


class SecureRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user", min_length=1)
    request: str = Field(..., description="Natural language user request prompt", min_length=1)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def check_forbidden_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            found_forbidden = [key for key in data.keys() if key in FORBIDDEN_CLIENT_FIELDS]
            if found_forbidden:
                raise ValueError(
                    f"Forbidden client security parameters supplied: {', '.join(found_forbidden)}. "
                    "Authorization decision fields cannot be client-controlled."
                )
        return data
