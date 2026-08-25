import logging
from typing import Optional
from fastapi import HTTPException, status
from app.approval.repository import ApprovalTicket, in_memory_approval_repo

logger = logging.getLogger(__name__)


class HITLApprovalManager:
    @staticmethod
    async def create_ticket(
        approval_id: str,
        request_id: str,
        requester_id: str,
        intent: str,
        resource: str,
        policy_risk: str,
        tenant_id: str = "tenant_default",
    ) -> ApprovalTicket:
        return await in_memory_approval_repo.create_ticket(
            approval_id=approval_id,
            request_id=request_id,
            requester_id=requester_id,
            intent=intent,
            resource=resource,
            policy_risk=policy_risk,
            tenant_id=tenant_id,
        )

    @staticmethod
    async def approve(approval_id: str, approver_id: str, tenant_id: Optional[str] = None) -> ApprovalTicket:
        ticket = await in_memory_approval_repo.get_ticket(approval_id, tenant_id=tenant_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval ticket '{approval_id}' not found."
            )

        # Self-approval prevention rule
        if ticket.requester_id == approver_id:
            logger.warning(
                f"Self-approval attempt blocked: Requester '{ticket.requester_id}' tried to approve ticket '{approval_id}'."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Self-approval forbidden: Requester cannot self-approve their own request."
            )

        if ticket.is_expired():
            await in_memory_approval_repo.update_ticket_status(approval_id, "EXPIRED", approver_id, tenant_id=tenant_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Approval ticket '{approval_id}' has expired."
            )

        if ticket.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Approval ticket '{approval_id}' was {ticket.status.lower()} and cannot be reused. It has already been {ticket.status.lower()}."
            )

        return await in_memory_approval_repo.update_ticket_status(approval_id, "APPROVED", approver_id, tenant_id=tenant_id)

    @staticmethod
    async def reject(approval_id: str, approver_id: str, tenant_id: Optional[str] = None) -> ApprovalTicket:
        ticket = await in_memory_approval_repo.get_ticket(approval_id, tenant_id=tenant_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval ticket '{approval_id}' not found."
            )

        if ticket.is_expired():
            await in_memory_approval_repo.update_ticket_status(approval_id, "EXPIRED", approver_id, tenant_id=tenant_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Approval ticket '{approval_id}' has expired."
            )

        if ticket.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Approval ticket '{approval_id}' was {ticket.status.lower()} and cannot be reused. It has already been {ticket.status.lower()}."
            )

        return await in_memory_approval_repo.update_ticket_status(approval_id, "REJECTED", approver_id, tenant_id=tenant_id)


approval_manager = HITLApprovalManager()
