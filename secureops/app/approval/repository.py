from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from fastapi import HTTPException, status
from app.config import settings


class ApprovalTicket:
    def __init__(
        self,
        approval_id: str,
        request_id: str,
        requester_id: str,
        intent: str,
        resource: str,
        policy_risk: str,
        tenant_id: str = "tenant_default",
        expiry_minutes: int = settings.APPROVAL_EXPIRY_MINUTES,
    ):
        self.approval_id = approval_id
        self.request_id = request_id
        self.requester_id = requester_id
        self.intent = intent
        self.resource = resource
        self.policy_risk = policy_risk
        self.tenant_id = tenant_id
        self.status = "PENDING"  # PENDING, APPROVED, REJECTED, EXPIRED
        self.approver_id: Optional[str] = None
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.expires_at = self.created_at + timedelta(minutes=expiry_minutes)

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at


class InMemoryApprovalRepository:
    def __init__(self):
        self.tickets: Dict[str, ApprovalTicket] = {}

    async def create_ticket(
        self,
        approval_id: str,
        request_id: str,
        requester_id: str,
        intent: str,
        resource: str,
        policy_risk: str,
        tenant_id: str = "tenant_default",
    ) -> ApprovalTicket:
        ticket = ApprovalTicket(
            approval_id=approval_id,
            request_id=request_id,
            requester_id=requester_id,
            intent=intent,
            resource=resource,
            policy_risk=policy_risk,
            tenant_id=tenant_id,
        )
        self.tickets[approval_id] = ticket
        return ticket

    async def get_ticket(self, approval_id: str, tenant_id: Optional[str] = None) -> Optional[ApprovalTicket]:
        ticket = self.tickets.get(approval_id)
        if not ticket:
            return None
        if tenant_id and ticket.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cross-tenant access forbidden: Approval ticket '{approval_id}' belongs to tenant '{ticket.tenant_id}', not '{tenant_id}'."
            )
        return ticket

    async def list_tickets(self, tenant_id: Optional[str] = None, status_filter: Optional[str] = None) -> List[ApprovalTicket]:
        results = list(self.tickets.values())
        if tenant_id:
            results = [t for t in results if t.tenant_id == tenant_id]
        if status_filter:
            results = [t for t in results if t.status == status_filter.upper()]
        return results

    async def update_ticket_status(
        self,
        approval_id: str,
        new_status: str,
        approver_id: str,
        tenant_id: Optional[str] = None,
    ) -> ApprovalTicket:
        ticket = await self.get_ticket(approval_id, tenant_id=tenant_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval ticket '{approval_id}' not found."
            )

        ticket.status = new_status
        ticket.approver_id = approver_id
        ticket.updated_at = datetime.now(timezone.utc)
        return ticket


in_memory_approval_repo = InMemoryApprovalRepository()
