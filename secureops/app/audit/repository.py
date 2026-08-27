import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from app.audit.logger import redact_sensitive_data

logger = logging.getLogger(__name__)


class AuditRecord(dict):
    def __init__(
        self,
        request_id: str,
        user_id: str,
        intent: str,
        resource: str,
        ai_risk: str,
        policy_risk: str,
        final_decision: str,
        provider: str,
        fallback_used: bool,
        latency_ms: float,
        tenant_id: str = "tenant_default",
        error_status: Optional[str] = None,
    ):
        data = {
            "request_id": request_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "intent": intent,
            "resource": resource,
            "ai_risk": ai_risk,
            "policy_risk": policy_risk,
            "final_decision": final_decision,
            "provider": provider,
            "fallback_used": fallback_used,
            "latency_ms": latency_ms,
            "error_status": error_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        super().__init__(data)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self)

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'AuditRecord' object has no attribute '{name}'")


class BaseAuditRepository(ABC):
    @abstractmethod
    async def save_audit_log(
        self,
        request_id: str,
        user_id: str,
        intent: str,
        resource: str,
        ai_risk: str,
        policy_risk: str,
        final_decision: str,
        provider: str,
        fallback_used: bool,
        latency_ms: float,
        tenant_id: str = "tenant_default",
        error_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def list_audit_events(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        pass


class InMemoryAuditRepository(BaseAuditRepository):
    def __init__(self):
        self.logs: List[AuditRecord] = []

    async def save_audit_log(
        self,
        request_id: str,
        user_id: str,
        intent: str,
        resource: str,
        ai_risk: str,
        policy_risk: str,
        final_decision: str,
        provider: str,
        fallback_used: bool,
        latency_ms: float,
        tenant_id: str = "tenant_default",
        error_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        record = AuditRecord(
            request_id=request_id,
            tenant_id=tenant_id,
            user_id=user_id,
            intent=intent,
            resource=resource,
            ai_risk=ai_risk,
            policy_risk=policy_risk,
            final_decision=final_decision,
            provider=provider,
            fallback_used=fallback_used,
            latency_ms=latency_ms,
            error_status=error_status,
        )

        redacted_payload = redact_sensitive_data(record.to_dict())
        self.logs.append(record)

        log_json = json.dumps({
            "event_type": "SECURITY_AUDIT_LOG",
            "timestamp": record["timestamp"],
            **redacted_payload,
        })
        logger.info(log_json)

        return redacted_payload

    async def list_audit_events(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        results = [l for l in self.logs if l["tenant_id"] == tenant_id]
        if user_id:
            results = [l for l in results if l["user_id"] == user_id]
        if request_id:
            results = [l for l in results if l["request_id"] == request_id]
        if decision:
            results = [l for l in results if l["final_decision"] == decision.upper()]

        return [redact_sensitive_data(l.to_dict()) for l in results[-limit:]]


class PostgresAuditRepository(BaseAuditRepository):
    def __init__(self, fallback_repo: Optional[InMemoryAuditRepository] = None):
        self.fallback_repo = fallback_repo or InMemoryAuditRepository()

    async def save_audit_log(
        self,
        request_id: str,
        user_id: str,
        intent: str,
        resource: str,
        ai_risk: str,
        policy_risk: str,
        final_decision: str,
        provider: str,
        fallback_used: bool,
        latency_ms: float,
        tenant_id: str = "tenant_default",
        error_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Always log to in-memory fallback for test runner inspection & fast retrieval
        in_mem_res = await self.fallback_repo.save_audit_log(
            request_id=request_id,
            user_id=user_id,
            intent=intent,
            resource=resource,
            ai_risk=ai_risk,
            policy_risk=policy_risk,
            final_decision=final_decision,
            provider=provider,
            fallback_used=fallback_used,
            latency_ms=latency_ms,
            tenant_id=tenant_id,
            error_status=error_status,
        )

        try:
            from app.db.session import async_session_factory
            from app.db.models import AuditLogModel
            async with async_session_factory() as session:
                log_entry = AuditLogModel(
                    request_id=request_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    intent=intent,
                    resource=resource,
                    ai_risk=ai_risk,
                    policy_risk=policy_risk,
                    final_decision=final_decision,
                    provider=provider,
                    fallback_used=fallback_used,
                    latency_ms=latency_ms,
                    error_status=error_status,
                )
                session.add(log_entry)
                await session.commit()
        except Exception as exc:
            logger.debug(f"PostgreSQL audit save skipped/failed ({exc}); fallback record retained.")

        return in_mem_res

    async def list_audit_events(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        try:
            from app.db.session import async_session_factory
            from app.db.models import AuditLogModel
            from sqlalchemy import select
            async with async_session_factory() as session:
                stmt = select(AuditLogModel).where(AuditLogModel.tenant_id == tenant_id)
                if user_id:
                    stmt = stmt.where(AuditLogModel.user_id == user_id)
                if request_id:
                    stmt = stmt.where(AuditLogModel.request_id == request_id)
                if decision:
                    stmt = stmt.where(AuditLogModel.final_decision == decision.upper())
                stmt = stmt.order_by(AuditLogModel.id.desc()).limit(limit)

                res = await session.execute(stmt)
                db_logs = res.scalars().all()
                if db_logs:
                    events = []
                    for item in reversed(db_logs):
                        dict_item = {
                            "request_id": item.request_id,
                            "tenant_id": item.tenant_id,
                            "user_id": item.user_id,
                            "intent": item.intent,
                            "resource": item.resource,
                            "ai_risk": item.ai_risk,
                            "policy_risk": item.policy_risk,
                            "final_decision": item.final_decision,
                            "provider": item.provider,
                            "fallback_used": item.fallback_used,
                            "latency_ms": item.latency_ms,
                            "error_status": item.error_status,
                            "timestamp": item.timestamp.isoformat() if item.timestamp else datetime.now(timezone.utc).isoformat(),
                        }
                        events.append(redact_sensitive_data(dict_item))
                    return events
        except Exception as exc:
            logger.debug(f"PostgreSQL audit list query skipped/failed ({exc}); using fallback repository.")

        return await self.fallback_repo.list_audit_events(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            decision=decision,
            limit=limit,
        )


_raw_in_memory_audit_repo = InMemoryAuditRepository()
postgres_audit_repo = PostgresAuditRepository(fallback_repo=_raw_in_memory_audit_repo)
audit_repository = postgres_audit_repo
in_memory_audit_repo = postgres_audit_repo  # Direct legacy references to PostgresAuditRepository
