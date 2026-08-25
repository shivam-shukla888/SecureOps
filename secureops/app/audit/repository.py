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


in_memory_audit_repo = InMemoryAuditRepository()
