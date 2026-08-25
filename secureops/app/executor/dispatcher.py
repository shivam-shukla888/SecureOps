import time
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.decision import PolicyDecision, DecisionEnum
from app.tools.registry import ToolRegistry
from app.tools.permissions import ToolPermissionEngine
from app.approval.repository import in_memory_approval_repo
from app.security.idempotency import idempotency_manager
from app.audit.repository import in_memory_audit_repo

logger = logging.getLogger(__name__)


class ExecutionDispatcher:
    @staticmethod
    def dispatch(decision: PolicyDecision) -> Dict[str, Any]:
        """
        Simulated dispatcher (Phase 1 & Phase 2 backward compatibility).
        """
        if decision.decision == DecisionEnum.ALLOW:
            return {
                "status": "executed",
                "message": f"Successfully executed safe operation '{decision.intent.value}' on resource '{decision.resource}'.",
                "simulated": True,
            }
        elif decision.decision == DecisionEnum.REQUIRE_APPROVAL:
            return {
                "status": "pending_approval",
                "message": f"Operation '{decision.intent.value}' on resource '{decision.resource}' requires approval. Ticket routed to approval workflow.",
                "requires_approval": True,
                "simulated": True,
            }
        else:  # BLOCK
            return {
                "status": "blocked",
                "message": f"Operation '{decision.intent.value}' rejected by security policy.",
                "reason": decision.reason,
                "simulated": True,
            }

    @staticmethod
    async def execute_tool(
        request_id: str,
        user_id: str,
        policy_decision: PolicyDecision,
        tool_input: Dict[str, Any],
        approval_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        tenant_id: str = "tenant_default",
    ) -> Dict[str, Any]:
        start_time = time.time()
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"

        # 1. Idempotency check
        if idempotency_key:
            cached = idempotency_manager.get_record(user_id, idempotency_key)
            if cached:
                return cached

        # 2. Derive Tool from Policy Decision Intent (Client CANNOT pick tool)
        tool_def = ToolRegistry.get_tool_for_intent(policy_decision.intent)

        # 3. Retrieve Approval Ticket if approval_id provided
        approval_ticket = None
        if approval_id:
            approval_ticket = await in_memory_approval_repo.get_ticket(approval_id)

        # 4. Extract target resource for binding validation
        target_resource = tool_input.get("target_resource") or tool_input.get("query") or tool_input.get("document_id") or policy_decision.resource

        # 5. Server-side Tool Permission Engine Validation
        ToolPermissionEngine.validate_tool_execution_permission(
            tool_def=tool_def,
            policy_decision=policy_decision,
            approval_ticket=approval_ticket,
            user_id=user_id,
            request_id=request_id,
            target_resource=target_resource,
        )

        # 6. Validate Tool Input against Pydantic schema (extra="forbid", path traversal, command injection)
        # Strip client-supplied security fields ('intent', 'tenant_id') to enforce server-side authority
        clean_tool_input = {k: v for k, v in tool_input.items() if k not in ["intent", "tenant_id"]}
        try:
            validated_inputs = tool_def.input_schema(**clean_tool_input)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tool input validation error for tool '{tool_def.name}': {str(exc)}"
            )

        # 7. Execute Tool Handler with Timeout Control
        try:
            import inspect
            sig = inspect.signature(tool_def.handler)
            if "tenant_id" in sig.parameters:
                coro = tool_def.handler(validated_inputs, tenant_id=tenant_id)
            else:
                coro = tool_def.handler(validated_inputs)

            result = await asyncio.wait_for(
                coro,
                timeout=settings.EXECUTION_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.error(f"Tool execution for '{tool_def.name}' timed out after {settings.EXECUTION_TIMEOUT_SECONDS}s.")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Tool execution timed out after {settings.EXECUTION_TIMEOUT_SECONDS} seconds."
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Tool handler error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Tool execution failed: {str(exc)}"
            )

        latency_ms = (time.time() - start_time) * 1000.0

        response_payload = {
            "execution_id": execution_id,
            "request_id": request_id,
            "status": "executed",
            "tool_name": tool_def.name,
            "result": result,
            "latency_ms": round(latency_ms, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 8. Save Idempotency Cache Record
        if idempotency_key:
            idempotency_manager.save_record(user_id, idempotency_key, response_payload)

        # 9. Audit Event Logging
        await in_memory_audit_repo.save_audit_log(
            request_id=request_id,
            user_id=user_id,
            intent=policy_decision.intent.value,
            resource=target_resource,
            ai_risk=policy_decision.ai_risk.value,
            policy_risk=policy_decision.policy_risk.value,
            final_decision="EXECUTED",
            provider=f"tool:{tool_def.name}",
            fallback_used=False,
            latency_ms=latency_ms,
        )

        return response_payload
