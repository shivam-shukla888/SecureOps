from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DashboardSummaryResponse(BaseModel):
    tenant_id: str = Field(..., description="Unique identifier of the tenant")
    user_id: str = Field(..., description="Unique identifier of the authenticated user")
    role: str = Field(..., description="RBAC role of the authenticated user")
    requests_today: int = Field(0, description="Total number of requests processed today")
    allowed_requests: int = Field(0, description="Total number of policy-allowed requests")
    blocked_requests: int = Field(0, description="Total number of policy-blocked requests")
    pending_approvals: int = Field(0, description="Number of tickets currently awaiting HITL approval")
    security_events: int = Field(0, description="Number of security events recorded for the tenant")
    provider_fallbacks: int = Field(0, description="Number of times an AI provider fallback was triggered")
    metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Application performance and latency metrics summary")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of summary generation")
