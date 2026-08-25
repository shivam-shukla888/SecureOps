import logging
from typing import Optional
from fastapi import HTTPException, status

from app.schemas.decision import PolicyDecision, DecisionEnum
from app.tools.base import ToolDefinition
from app.approval.repository import ApprovalTicket

logger = logging.getLogger(__name__)


class ToolPermissionEngine:
    @staticmethod
    def validate_tool_execution_permission(
        tool_def: Optional[ToolDefinition],
        policy_decision: PolicyDecision,
        approval_ticket: Optional[ApprovalTicket] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        target_resource: Optional[str] = None,
    ) -> None:
        # 1. Tool existence check
        if not tool_def:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No authorized tool registered for intent '{policy_decision.intent.value}'."
            )

        # 2. Intent match check
        if tool_def.required_intent != policy_decision.intent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Tool '{tool_def.name}' requires intent '{tool_def.required_intent.value}', but request intent is '{policy_decision.intent.value}'."
            )

        # 3. Policy decision status check
        if policy_decision.decision == DecisionEnum.BLOCK:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Operation rejected by security policy ({policy_decision.reason})."
            )

        # 4. Approval binding validation if approval is required
        needs_approval = tool_def.requires_approval or policy_decision.requires_approval

        if needs_approval:
            if not approval_ticket:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: Tool '{tool_def.name}' requires a valid approved ticket ID (approval_id)."
                )

            # Ticket state checks
            if approval_ticket.status != "APPROVED":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: Approval ticket '{approval_ticket.approval_id}' status is '{approval_ticket.status}', not 'APPROVED'."
                )

            if approval_ticket.is_expired():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Permission denied: Approval ticket '{approval_ticket.approval_id}' has expired."
                )

            # Cryptographic / Logical Binding Checks
            if request_id and approval_ticket.request_id != request_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Approval binding error: Ticket '{approval_ticket.approval_id}' was issued for request '{approval_ticket.request_id}', not '{request_id}'."
                )

            if user_id and approval_ticket.requester_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Approval binding error: Ticket '{approval_ticket.approval_id}' belongs to requester '{approval_ticket.requester_id}', not '{user_id}'."
                )

            if approval_ticket.intent != policy_decision.intent.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Approval binding error: Ticket was approved for intent '{approval_ticket.intent}', not '{policy_decision.intent.value}'."
                )

            if target_resource and approval_ticket.resource != target_resource:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Approval binding error: Ticket was approved for resource '{approval_ticket.resource}', not '{target_resource}'."
                )
