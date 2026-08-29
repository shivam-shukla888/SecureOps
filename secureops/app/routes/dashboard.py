import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request

from app.schemas.dashboard import DashboardSummaryResponse
from app.security.auth import verify_api_key
from app.security.rbac import TenantUserContext
from app.audit.repository import in_memory_audit_repo
from app.approval.repository import in_memory_approval_repo
from app.audit.siem import siem_manager
from app.audit.metrics import metrics_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get multi-tenant dashboard summary telemetry",
    description="Retrieves live, tenant-scoped request counts, approval statuses, security events, provider fallbacks, and performance metrics for the authenticated user.",
)
async def get_dashboard_summary(
    request: Request,
    api_key: str = Depends(verify_api_key),
) -> DashboardSummaryResponse:
    ctx: TenantUserContext = request.state.user_context

    # Retrieve tenant-scoped telemetry
    audit_events = await in_memory_audit_repo.list_audit_events(tenant_id=ctx.tenant_id, limit=500)
    tickets = await in_memory_approval_repo.list_tickets(tenant_id=ctx.tenant_id)
    sec_events = siem_manager.list_tenant_security_events(tenant_id=ctx.tenant_id)

    # Compute accurate operational counts
    allowed = sum(1 for e in audit_events if e.get("final_decision") == "ALLOW")
    blocked = sum(1 for e in audit_events if e.get("final_decision") == "BLOCK")
    pending = sum(1 for t in tickets if getattr(t, "status", None) == "PENDING")
    fallbacks = sum(1 for e in audit_events if e.get("fallback_used"))

    # Fetch live performance metrics
    metrics = metrics_tracker.get_summary()

    return DashboardSummaryResponse(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        role=ctx.role.value if hasattr(ctx.role, "value") else str(ctx.role),
        requests_today=len(audit_events),
        allowed_requests=allowed,
        blocked_requests=blocked,
        pending_approvals=pending,
        security_events=len(sec_events),
        provider_fallbacks=fallbacks,
        metrics=metrics,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
