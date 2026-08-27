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


class PostgresApprovalRepository:
    def __init__(self, fallback_repo: Optional[InMemoryApprovalRepository] = None):
        self.fallback_repo = fallback_repo or InMemoryApprovalRepository()

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
        ticket = await self.fallback_repo.create_ticket(
            approval_id=approval_id,
            request_id=request_id,
            requester_id=requester_id,
            intent=intent,
            resource=resource,
            policy_risk=policy_risk,
            tenant_id=tenant_id,
        )

        try:
            from app.db.session import async_session_factory
            from app.db.models import ApprovalTicketModel
            async with async_session_factory() as session:
                db_ticket = ApprovalTicketModel(
                    approval_id=approval_id,
                    request_id=request_id,
                    tenant_id=tenant_id,
                    requester_id=requester_id,
                    intent=intent,
                    resource=resource,
                    policy_risk=policy_risk,
                    status=ticket.status,
                    created_at=ticket.created_at,
                    expires_at=ticket.expires_at,
                    updated_at=ticket.updated_at,
                )
                session.add(db_ticket)
                await session.commit()
        except Exception:
            pass

        return ticket

    async def get_ticket(self, approval_id: str, tenant_id: Optional[str] = None) -> Optional[ApprovalTicket]:
        # Query PostgreSQL database first for authoritative persistence
        try:
            from app.db.session import async_session_factory
            from app.db.models import ApprovalTicketModel
            from sqlalchemy import select
            async with async_session_factory() as session:
                stmt = select(ApprovalTicketModel).where(ApprovalTicketModel.approval_id == approval_id)
                res = await session.execute(stmt)
                db_ticket = res.scalar_one_or_none()
                if db_ticket:
                    if tenant_id and db_ticket.tenant_id != tenant_id:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Cross-tenant access forbidden: Approval ticket '{approval_id}' belongs to tenant '{db_ticket.tenant_id}', not '{tenant_id}'."
                        )
                    t = ApprovalTicket(
                        approval_id=db_ticket.approval_id,
                        request_id=db_ticket.request_id,
                        requester_id=db_ticket.requester_id,
                        intent=db_ticket.intent,
                        resource=db_ticket.resource,
                        policy_risk=db_ticket.policy_risk,
                        tenant_id=db_ticket.tenant_id,
                    )
                    t.status = db_ticket.status
                    t.approver_id = db_ticket.approver_id
                    t.created_at = db_ticket.created_at
                    t.expires_at = db_ticket.expires_at
                    t.updated_at = db_ticket.updated_at
                    self.fallback_repo.tickets[t.approval_id] = t
                    return t
        except HTTPException:
            raise
        except Exception:
            pass

        return await self.fallback_repo.get_ticket(approval_id, tenant_id=tenant_id)

    async def list_tickets(self, tenant_id: Optional[str] = None, status_filter: Optional[str] = None) -> List[ApprovalTicket]:
        try:
            from app.db.session import async_session_factory
            from app.db.models import ApprovalTicketModel
            from sqlalchemy import select
            async with async_session_factory() as session:
                stmt = select(ApprovalTicketModel)
                if tenant_id:
                    stmt = stmt.where(ApprovalTicketModel.tenant_id == tenant_id)
                if status_filter:
                    stmt = stmt.where(ApprovalTicketModel.status == status_filter.upper())
                stmt = stmt.order_by(ApprovalTicketModel.created_at.desc())

                res = await session.execute(stmt)
                db_tickets = res.scalars().all()
                if db_tickets:
                    results = []
                    for db_t in db_tickets:
                        t = ApprovalTicket(
                            approval_id=db_t.approval_id,
                            request_id=db_t.request_id,
                            requester_id=db_t.requester_id,
                            intent=db_t.intent,
                            resource=db_t.resource,
                            policy_risk=db_t.policy_risk,
                            tenant_id=db_t.tenant_id,
                        )
                        t.status = db_t.status
                        t.approver_id = db_t.approver_id
                        t.created_at = db_t.created_at
                        t.expires_at = db_t.expires_at
                        t.updated_at = db_t.updated_at
                        self.fallback_repo.tickets[t.approval_id] = t
                        results.append(t)
                    return results
        except Exception:
            pass

        return await self.fallback_repo.list_tickets(tenant_id=tenant_id, status_filter=status_filter)

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
        self.fallback_repo.tickets[approval_id] = ticket

        try:
            from app.db.session import async_session_factory
            from app.db.models import ApprovalTicketModel
            from sqlalchemy import select
            async with async_session_factory() as session:
                stmt = select(ApprovalTicketModel).where(ApprovalTicketModel.approval_id == approval_id)
                res = await session.execute(stmt)
                db_ticket = res.scalar_one_or_none()
                if db_ticket:
                    db_ticket.status = new_status
                    db_ticket.approver_id = approver_id
                    db_ticket.updated_at = datetime.now(timezone.utc)
                    await session.commit()
        except Exception:
            pass

        return ticket


_raw_in_memory_approval_repo = InMemoryApprovalRepository()
postgres_approval_repo = PostgresApprovalRepository(fallback_repo=_raw_in_memory_approval_repo)
approval_repository = postgres_approval_repo
in_memory_approval_repo = postgres_approval_repo
