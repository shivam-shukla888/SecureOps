from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    request_id: str = Field(..., min_length=1, description="Original request ID")
    user_id: str = Field(..., min_length=1, description="Authenticated user ID")
    tool_input: Dict[str, Any] = Field(..., description="Tool input parameters matching tool input schema")
    approval_id: Optional[str] = Field(default=None, description="Approval ticket ID if required")


class ExecutionResponse(BaseModel):
    execution_id: str
    request_id: str
    status: str  # executed, failed, pending_approval, blocked
    tool_name: str
    result: Dict[str, Any]
    latency_ms: float
    timestamp: str
