import time
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class IdempotencyRecord:
    def __init__(self, key: str, tenant_id: str, user_id: str, result: Dict[str, Any], ttl_seconds: int = settings.IDEMPOTENCY_TTL_SECONDS):
        self.key = key
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.result = result
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_seconds

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class IdempotencyManager:
    def __init__(self):
        self.records: Dict[str, IdempotencyRecord] = {}

    def _composite_key(self, tenant_id: str, user_id: str, idempotency_key: str) -> str:
        return f"{tenant_id}:{user_id}:{idempotency_key}"

    def get_record(self, user_id: str, idempotency_key: str, tenant_id: str = "tenant_default") -> Optional[Dict[str, Any]]:
        if not idempotency_key:
            return None

        comp_key = self._composite_key(tenant_id, user_id, idempotency_key)
        record = self.records.get(comp_key)

        if not record:
            return None

        if record.is_expired():
            del self.records[comp_key]
            return None

        logger.info(f"Idempotency hit for tenant '{tenant_id}' user '{user_id}' key '{idempotency_key}'. Returning cached result.")
        return record.result

    def save_record(self, user_id: str, idempotency_key: str, result: Dict[str, Any], tenant_id: str = "tenant_default"):
        if not idempotency_key:
            return

        comp_key = self._composite_key(tenant_id, user_id, idempotency_key)
        self.records[comp_key] = IdempotencyRecord(
            key=idempotency_key,
            tenant_id=tenant_id,
            user_id=user_id,
            result=result,
        )


idempotency_manager = IdempotencyManager()
