from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ApprovalTicketResponse(BaseModel):
    approval_id: str
    request_id: str
    requester_id: str
    intent: str
    resource: str
    policy_risk: str
    status: str  # PENDING, APPROVED, REJECTED, EXPIRED
    expires_at: str
    created_at: str


class ApprovalActionRequest(BaseModel):
    approver_id: str = Field(..., description="Unique user ID of the approving security officer", min_length=1)
    notes: Optional[str] = Field(default="", description="Optional approval notes")


class ApprovalActionResultResponse(BaseModel):
    request_id: str
    approval_id: str
    decision: str  # APPROVED, REJECTED, EXPIRED
    status: str
    message: str
    approver_id: str
    timestamp: str
    execution_result: Optional[Dict[str, Any]] = None
