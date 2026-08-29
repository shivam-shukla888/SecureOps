import time
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import FastAPI, Depends, Request, HTTPException, Header, Query, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings, validate_production_config
from app.schemas.request import SecureRequest
from app.schemas.decision import (
    SecurityGatewayResponse,
    DecisionEnum,
    ClassifierResult,
    IntentEnum,
    RiskEnum,
)
from app.schemas.approval import (
    ApprovalActionRequest,
    ApprovalActionResultResponse,
)
from app.schemas.execution import ExecutionRequest, ExecutionResponse
from app.security.auth import verify_api_key
from app.security.rbac import RoleEnum, require_role, TenantUserContext
from app.security.credentials import credential_repo, APICredentialRecord
from app.security.validation import (
    validate_request_payload_size,
    validate_request_text_length,
)
from app.security.rate_limit import check_rate_limit, rate_limiter_instance
from app.security.policy import DeterministicPolicyEngine
from app.security.headers import SecurityHeadersMiddleware
from app.ai.classifier import RequestClassifier
from app.executor.dispatcher import ExecutionDispatcher
from app.audit.repository import in_memory_audit_repo
from app.audit.metrics import metrics_tracker
from app.audit.security_events import SecurityEvent, SecurityEventType, SeverityEnum
from app.audit.siem import siem_manager
from app.approval.manager import approval_manager
from app.approval.repository import in_memory_approval_repo
from app.n8n.webhook import n8n_webhook_client
from app.tools.integrations.document_service import document_service_adapter, DocumentSearchRequest

from contextlib import asynccontextmanager
from app.security.redis_service import redis_service

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Validates configuration presence and logs sanitized startup status."""
    validate_production_config()
    print("===============================================================================")
    print("                    SECUREOPS ENTERPRISE GATEWAY STARTUP                       ")
    print("===============================================================================")
    print(f"  ENVIRONMENT            : {settings.ENVIRONMENT}")
    print(f"  LOG_LEVEL              : {settings.LOG_LEVEL}")
    print(f"  API_KEY                : {'CONFIGURED' if settings.API_KEY else 'MISSING'}")
    print(f"  DATABASE               : {'CONFIGURED' if settings.DATABASE_URL else 'MISSING'}")
    print(f"  REDIS                  : {'CONFIGURED' if (settings.is_upstash_configured or settings.has_remote_redis or settings.REDIS_URL) else 'MISSING'}")
    print(f"  UPSTASH_REDIS          : {'CONFIGURED' if settings.is_upstash_configured else 'MISSING'}")
    print(f"  RATE_LIMIT_BACKEND     : {settings.RATE_LIMIT_BACKEND}")
    print(f"  GEMINI_API_KEY         : {'CONFIGURED' if settings.GEMINI_API_KEY else 'MISSING'}")
    print(f"  GROQ_API_KEY           : {'CONFIGURED' if settings.GROQ_API_KEY else 'MISSING'}")
    print(f"  N8N_APPROVAL_WEBHOOK   : {'CONFIGURED' if settings.N8N_APPROVAL_WEBHOOK_URL else 'MISSING'}")
    print(f"  CORS CONFIGURED        : True")
    print(f"  CORS ORIGINS COUNT     : {len(settings.cors_origins_list)}")
    print("===============================================================================")
    if settings.ENVIRONMENT.lower() != "production":
        print("  REGISTERED API ROUTES:")
        for route in app_instance.routes:
            if hasattr(route, "methods") and hasattr(route, "path"):
                methods = ", ".join(sorted(route.methods - {"HEAD"}))
                if methods:
                    print(f"    {methods:<16} {route.path}")
        print("===============================================================================\n")
    yield

from fastapi.middleware.cors import CORSMiddleware

from app.routes.agents import router as agents_router
from app.routes.evaluations import router as evaluations_router
from app.routes.benchmarks import router as benchmarks_router
from app.routes.dashboard import router as dashboard_router

app = FastAPI(
    title="SecureOps Gateway API",
    description="Enterprise Multi-Tenant AI Gateway, Deterministic Policy Engine, Hashed Credential Manager & Secure Executor",
    version="5.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(agents_router)
app.include_router(evaluations_router)
app.include_router(benchmarks_router)
app.include_router(dashboard_router)

# Global exception handlers & middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "Accept", "Origin"],
    expose_headers=["X-Request-ID", "Strict-Transport-Security", "X-Content-Type-Options", "X-Frame-Options"],
    max_age=600,
)
app.add_middleware(SecurityHeadersMiddleware)


# Exception Handlers for Unified JSON Error Output
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    ctx: Optional[TenantUserContext] = getattr(request.state, "user_context", None)
    tenant_id = ctx.tenant_id if ctx else "tenant_default"
    user_id = ctx.user_id if ctx else None

    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        metrics_tracker.record_auth_failure()
        await siem_manager.record_security_event(
            SecurityEvent(
                event_type=SecurityEventType.AUTH_FAILURE,
                severity=SeverityEnum.HIGH,
                tenant_id=tenant_id,
                user_id=user_id,
                metadata={"detail": exc.detail},
            )
        )
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        await siem_manager.record_security_event(
            SecurityEvent(
                event_type=SecurityEventType.AUTHZ_FAILURE,
                severity=SeverityEnum.HIGH,
                tenant_id=tenant_id,
                user_id=user_id,
                metadata={"detail": exc.detail},
            )
        )
    elif exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        metrics_tracker.record_rate_limit()
        await siem_manager.record_security_event(
            SecurityEvent(
                event_type=SecurityEventType.RATE_LIMIT_TRIGGERED,
                severity=SeverityEnum.MEDIUM,
                tenant_id=tenant_id,
                user_id=user_id,
                metadata={"detail": exc.detail},
            )
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "status_code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        },
        headers=exc.headers,
    )


@app.get("/health", tags=["Health & Status"])
async def health_check():
    """Basic application liveness check."""
    return {
        "status": "healthy",
        "service": "SecureOps API Gateway",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Health & Status"])
async def readiness_check():
    """Readiness check testing rate limiter, PostgreSQL connectivity, Redis, and metrics based on REAL connectivity."""
    from app.db.session import check_db_connectivity
    db_ok = await check_db_connectivity()

    is_prod = str(getattr(settings, "ENVIRONMENT", "development")).lower() == "production"

    redis_ok = False
    if redis_service.is_configured:
        redis_ok = await redis_service.ping()
    elif not is_prod:
        redis_ok = True

    limiter_ok = False
    try:
        is_limited = await rate_limiter_instance.is_rate_limited("readiness_check")
        if is_prod:
            limiter_ok = redis_ok and not is_limited
        else:
            limiter_ok = not is_limited
    except Exception as exc:
        logger.warning(f"Rate limiter readiness check failed: {exc}")
        limiter_ok = False

    metrics_summary = metrics_tracker.get_summary()
    overall_ready = db_ok and redis_ok and limiter_ok

    if redis_ok:
        redis_status = "ready"
    elif redis_service.is_configured or is_prod:
        redis_status = "unhealthy"
    else:
        redis_status = "unconfigured"

    return {
        "status": "ready" if overall_ready else "degraded",
        "rate_limiter": "ready" if limiter_ok else "unhealthy",
        "database": "ready" if db_ok else "unhealthy",
        "redis": redis_status,
        "metrics_summary": metrics_summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/v1/requests", response_model=SecurityGatewayResponse, tags=["Security Gateway"])
async def process_request(
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    start_time = time.time()
    ctx: TenantUserContext = request.state.user_context
    request_id = f"req_{uuid.uuid4().hex[:12]}"

    # Rate Limiting Check
    await check_rate_limit(identifier=f"{ctx.tenant_id}:{ctx.user_id}")

    # Payload size & Content-Type validation
    await validate_request_payload_size(request)

    # Parse JSON body
    try:
        body_json = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed request: Invalid JSON body."
        )

    # Pydantic validation (rejects client-controlled security fields & verifies user_id/request)
    try:
        secure_req = SecureRequest(**body_json)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed request: {str(ve)}"
        )

    # Text length check
    validate_request_text_length(secure_req.request)

    # AI Classification (Gemini -> Groq Fallback Chain)
    classifier = RequestClassifier()
    ai_result, ai_success, provider_used, fallback_used = await classifier.classify(secure_req.request)

    # Deterministic Policy Evaluation
    policy_decision = DeterministicPolicyEngine.evaluate(ai_result)

    if policy_decision.override_applied:
        await siem_manager.record_security_event(
            SecurityEvent(
                event_type=SecurityEventType.POLICY_OVERRIDE,
                severity=SeverityEnum.MEDIUM,
                tenant_id=ctx.tenant_id,
                user_id=secure_req.user_id,
                request_id=request_id,
                metadata={"reason": policy_decision.reason, "intent": policy_decision.intent.value},
            )
        )

    approval_id = None
    expires_at_str = None

    # Human-In-The-Loop Approval Ticket Creation (if REQUIRE_APPROVAL)
    if policy_decision.decision == DecisionEnum.REQUIRE_APPROVAL:
        approval_id = f"appr_{uuid.uuid4().hex[:12]}"
        ticket = await approval_manager.create_ticket(
            approval_id=approval_id,
            request_id=request_id,
            requester_id=secure_req.user_id,
            intent=policy_decision.intent.value,
            resource=policy_decision.resource,
            policy_risk=policy_decision.policy_risk.value,
            tenant_id=ctx.tenant_id,
        )
        expires_at_str = ticket.expires_at.isoformat()

        # Outbound HMAC-signed n8n webhook notification
        await n8n_webhook_client.dispatch_approval_request(
            request_id=request_id,
            approval_id=approval_id,
            user_id=secure_req.user_id,
            intent=policy_decision.intent.value,
            resource=policy_decision.resource,
            policy_risk=policy_decision.policy_risk.value,
            expires_at=expires_at_str,
        )

    # Dispatch Execution (Real Tool Integration for SEARCH_DOCUMENT)
    if policy_decision.decision == DecisionEnum.ALLOW and policy_decision.intent == IntentEnum.SEARCH_DOCUMENT:
        search_query = secure_req.request if ("architecture" in secure_req.request.lower() or "search" in secure_req.request.lower()) else (policy_decision.resource or secure_req.request)
        search_req = DocumentSearchRequest(
            query=search_query,
            tenant_id=ctx.tenant_id,
        )
        execution_result = await document_service_adapter.search_documents(search_req)
    else:
        execution_result = ExecutionDispatcher.dispatch(policy_decision)

    if approval_id:
        execution_result["approval_id"] = approval_id
        execution_result["expires_at"] = expires_at_str

    latency_ms = (time.time() - start_time) * 1000.0

    # Record Metrics & Audit Log
    metrics_tracker.record_request(
        decision=policy_decision.decision.value,
        latency_ms=latency_ms,
        fallback_used=fallback_used,
    )

    await in_memory_audit_repo.save_audit_log(
        request_id=request_id,
        user_id=secure_req.user_id,
        intent=policy_decision.intent.value,
        resource=policy_decision.resource,
        ai_risk=ai_result.risk.value,
        policy_risk=policy_decision.policy_risk.value,
        final_decision=policy_decision.decision.value,
        provider=provider_used,
        fallback_used=fallback_used,
        latency_ms=latency_ms,
        tenant_id=ctx.tenant_id,
        error_status="AI_CLASSIFICATION_FAILED" if not ai_success else None,
    )

    return SecurityGatewayResponse(
        request_id=request_id,
        user_id=secure_req.user_id,
        intent=policy_decision.intent,
        resource=policy_decision.resource,
        ai_risk=ai_result.risk,
        policy_risk=policy_decision.policy_risk,
        requires_approval=policy_decision.requires_approval,
        decision=policy_decision.decision,
        override_applied=policy_decision.override_applied,
        provider_used=provider_used,
        fallback_used=fallback_used,
        approval_id=approval_id,
        expires_at=expires_at_str,
        execution_result=execution_result,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/v1/executions", response_model=ExecutionResponse, tags=["Tool Executor"])
async def execute_tool_endpoint(
    request: Request,
    execution_req: ExecutionRequest,
    api_key: str = Depends(verify_api_key),
    idempotency_key: Optional[str] = Header(default=None, alias="idempotency-key"),
):
    ctx: TenantUserContext = request.state.user_context
    await check_rate_limit(identifier=f"{ctx.tenant_id}:{ctx.user_id}")
    await validate_request_payload_size(request)

    intent_hint = execution_req.tool_input.get("intent")
    target_resource = (
        execution_req.tool_input.get("target_resource")
        or execution_req.tool_input.get("query")
        or execution_req.tool_input.get("document_id")
        or "unknown"
    )

    try:
        if intent_hint:
            intent_enum = IntentEnum(str(intent_hint).upper())
        else:
            intent_enum = IntentEnum.UNKNOWN
    except ValueError:
        intent_enum = IntentEnum.UNKNOWN

    classifier_res = ClassifierResult(
        intent=intent_enum,
        resource=str(target_resource),
        risk=RiskEnum.HIGH if intent_enum == IntentEnum.UNKNOWN else RiskEnum.LOW,
        requires_approval=intent_enum in [IntentEnum.UPDATE_DATA, IntentEnum.SEND_DOCUMENT, IntentEnum.DELETE_DATA],
    )
    policy_decision = DeterministicPolicyEngine.evaluate(classifier_res)

    try:
        execution_result = await ExecutionDispatcher.execute_tool(
            request_id=execution_req.request_id,
            user_id=execution_req.user_id,
            policy_decision=policy_decision,
            tool_input=execution_req.tool_input,
            approval_id=execution_req.approval_id,
            idempotency_key=idempotency_key,
            tenant_id=ctx.tenant_id,
        )
        metrics_tracker.record_execution(success=True)
    except Exception as exc:
        metrics_tracker.record_execution(success=False)
        raise exc

    return ExecutionResponse(
        execution_id=execution_result["execution_id"],
        request_id=execution_result["request_id"],
        status=execution_result["status"],
        tool_name=execution_result["tool_name"],
        result=execution_result["result"],
        latency_ms=execution_result["latency_ms"],
        timestamp=execution_result["timestamp"],
    )


# --- HITL APPROVALS ENDPOINTS ---

@app.get("/v1/approvals", tags=["HITL Approvals"])
async def list_approvals(
    request: Request,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.APPROVER, RoleEnum.ADMIN, RoleEnum.OWNER])),
):
    tickets = await in_memory_approval_repo.list_tickets(tenant_id=ctx.tenant_id, status_filter=status_filter)
    return {
        "tenant_id": ctx.tenant_id,
        "count": len(tickets),
        "approvals": [
            {
                "approval_id": t.approval_id,
                "request_id": t.request_id,
                "requester_id": t.requester_id,
                "intent": t.intent,
                "resource": t.resource,
                "policy_risk": t.policy_risk,
                "status": t.status,
                "approver_id": t.approver_id,
                "created_at": t.created_at.isoformat(),
                "expires_at": t.expires_at.isoformat(),
            }
            for t in tickets
        ],
    }


@app.get("/v1/approvals/{approval_id}", tags=["HITL Approvals"])
async def get_approval_detail(
    approval_id: str,
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    ctx: TenantUserContext = request.state.user_context
    ticket = await in_memory_approval_repo.get_ticket(approval_id, tenant_id=ctx.tenant_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Approval ticket '{approval_id}' not found.")

    return {
        "approval_id": ticket.approval_id,
        "request_id": ticket.request_id,
        "requester_id": ticket.requester_id,
        "intent": ticket.intent,
        "resource": ticket.resource,
        "policy_risk": ticket.policy_risk,
        "status": ticket.status,
        "approver_id": ticket.approver_id,
        "created_at": ticket.created_at.isoformat(),
        "expires_at": ticket.expires_at.isoformat(),
    }


@app.post("/v1/approvals/{approval_id}/approve", response_model=ApprovalActionResultResponse, tags=["HITL Approvals"])
async def approve_request(
    approval_id: str,
    action_req: ApprovalActionRequest,
    request: Request,
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.APPROVER, RoleEnum.ADMIN, RoleEnum.OWNER])),
):
    ticket = await approval_manager.approve(
        approval_id=approval_id,
        approver_id=action_req.approver_id,
        tenant_id=ctx.tenant_id,
    )

    execution_sim = {
        "status": "executed_post_approval",
        "message": f"Operation '{ticket.intent}' on resource '{ticket.resource}' authorized and executed by approver '{ticket.approver_id}'.",
        "simulated": True,
    }

    return ApprovalActionResultResponse(
        request_id=ticket.request_id,
        approval_id=ticket.approval_id,
        decision="APPROVED",
        status="APPROVED",
        message=f"Request '{ticket.request_id}' successfully approved by security officer '{ticket.approver_id}'.",
        approver_id=ticket.approver_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        execution_result=execution_sim,
    )


@app.post("/v1/approvals/{approval_id}/reject", response_model=ApprovalActionResultResponse, tags=["HITL Approvals"])
async def reject_request(
    approval_id: str,
    action_req: ApprovalActionRequest,
    request: Request,
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.APPROVER, RoleEnum.ADMIN, RoleEnum.OWNER])),
):
    ticket = await approval_manager.reject(
        approval_id=approval_id,
        approver_id=action_req.approver_id,
        tenant_id=ctx.tenant_id,
    )

    execution_sim = {
        "status": "blocked",
        "message": f"Operation '{ticket.intent}' on resource '{ticket.resource}' explicitly rejected by security officer '{ticket.approver_id}'.",
        "simulated": True,
    }

    return ApprovalActionResultResponse(
        request_id=ticket.request_id,
        approval_id=ticket.approval_id,
        decision="REJECTED",
        status="REJECTED",
        message=f"Request '{ticket.request_id}' rejected by security officer '{ticket.approver_id}'.",
        approver_id=ticket.approver_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        execution_result=execution_sim,
    )


# --- AUDIT & SIEM API ENDPOINTS ---

@app.get("/v1/audit/events", tags=["Audit & Governance"])
async def list_audit_events(
    request: Request,
    user_id: Optional[str] = Query(default=None),
    request_id: Optional[str] = Query(default=None),
    decision: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.VIEWER, RoleEnum.OPERATOR, RoleEnum.APPROVER, RoleEnum.ADMIN, RoleEnum.OWNER])),
):
    events = await in_memory_audit_repo.list_audit_events(
        tenant_id=ctx.tenant_id,
        user_id=user_id,
        request_id=request_id,
        decision=decision,
        limit=limit,
    )
    return {
        "tenant_id": ctx.tenant_id,
        "count": len(events),
        "events": events,
    }


@app.get("/v1/security/events", tags=["Audit & Governance"])
async def list_security_events(
    request: Request,
    limit: int = Query(default=50, ge=1, le=500),
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.VIEWER, RoleEnum.OPERATOR, RoleEnum.APPROVER, RoleEnum.ADMIN, RoleEnum.OWNER])),
):
    events = siem_manager.list_tenant_security_events(tenant_id=ctx.tenant_id, limit=limit)
    return {
        "tenant_id": ctx.tenant_id,
        "count": len(events),
        "events": events,
    }


# --- CREDENTIAL MANAGEMENT API ENDPOINTS ---

@app.post("/v1/credentials", tags=["Credential Management"])
async def create_credential(
    request: Request,
    payload: dict,
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.ADMIN, RoleEnum.OWNER])),
):
    name = payload.get("name", "New API Credential")
    user_id = payload.get("user_id", ctx.user_id)
    role_str = payload.get("role", "OPERATOR")

    try:
        role_enum = RoleEnum(role_str.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role '{role_str}'. Valid roles: {[r.value for r in RoleEnum]}")

    raw_key, record = await credential_repo.create_credential(
        tenant_id=ctx.tenant_id,
        user_id=user_id,
        name=name,
        role=role_enum,
    )

    await siem_manager.record_security_event(
        SecurityEvent(
            event_type=SecurityEventType.CREDENTIAL_REVOKED,
            severity=SeverityEnum.INFO if hasattr(SeverityEnum, "INFO") else SeverityEnum.LOW,
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            metadata={"action": "CREATED_CREDENTIAL", "target_credential_id": record.credential_id},
        )
    )

    return {
        "status": "created",
        "api_key": raw_key,  # Returned ONCE on creation
        "credential": {
            "credential_id": record.credential_id,
            "tenant_id": record.tenant_id,
            "user_id": record.user_id,
            "name": record.name,
            "role": record.role.value,
            "created_at": record.created_at.isoformat(),
        },
        "warning": "Store this API key securely. It will not be shown again.",
    }


@app.post("/v1/credentials/{credential_id}/revoke", tags=["Credential Management"])
async def revoke_credential(
    credential_id: str,
    request: Request,
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.ADMIN, RoleEnum.OWNER])),
):
    record = await credential_repo.revoke_credential(credential_id, tenant_id=ctx.tenant_id)
    return {
        "status": "revoked",
        "credential_id": record.credential_id,
        "revoked_at": record.revoked_at.isoformat() if record.revoked_at else None,
    }


@app.post("/v1/credentials/{credential_id}/rotate", tags=["Credential Management"])
async def rotate_credential(
    credential_id: str,
    request: Request,
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.ADMIN, RoleEnum.OWNER])),
):
    raw_key, new_record = await credential_repo.rotate_credential(credential_id, tenant_id=ctx.tenant_id)
    return {
        "status": "rotated",
        "api_key": raw_key,
        "credential": {
            "credential_id": new_record.credential_id,
            "tenant_id": new_record.tenant_id,
            "user_id": new_record.user_id,
            "name": new_record.name,
            "role": new_record.role.value,
            "created_at": new_record.created_at.isoformat(),
        },
    }
