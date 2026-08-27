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


import json
from datetime import datetime, timezone, timedelta
from app.security.redis_service import redis_service

class IdempotencyManager:
    def __init__(self):
        self.records: Dict[str, IdempotencyRecord] = {}

    def _composite_key(self, tenant_id: str, user_id: str, idempotency_key: str) -> str:
        return f"{tenant_id}:{user_id}:{idempotency_key}"

    async def get_record(self, user_id: str, idempotency_key: str, tenant_id: str = "tenant_default") -> Optional[Dict[str, Any]]:
        if not idempotency_key:
            return None

        comp_key = self._composite_key(tenant_id, user_id, idempotency_key)
        record = self.records.get(comp_key)

        # 1. Check Redis cache if missing in memory
        if not record and redis_service.is_configured:
            try:
                cached_json = await redis_service.get(f"idempotency:{comp_key}")
                if cached_json:
                    parsed_result = json.loads(cached_json)
                    rec = IdempotencyRecord(
                        key=idempotency_key,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        result=parsed_result,
                    )
                    self.records[comp_key] = rec
                    record = rec
            except Exception as exc:
                logger.debug(f"Redis idempotency read skipped ({exc})")

        # 2. Query PostgreSQL database if missing in Redis & memory
        if not record:
            try:
                from app.db.session import async_session_factory
                from app.db.models import IdempotencyRecordModel
                from sqlalchemy import select
                async with async_session_factory() as session:
                    stmt = select(IdempotencyRecordModel).where(
                        IdempotencyRecordModel.tenant_id == tenant_id,
                        IdempotencyRecordModel.user_id == user_id,
                        IdempotencyRecordModel.idempotency_key == idempotency_key
                    )
                    res = await session.execute(stmt)
                    db_rec = res.scalar_one_or_none()

                    if db_rec:
                        parsed_result = json.loads(db_rec.response_json) if isinstance(db_rec.response_json, str) else db_rec.response_json
                        rec = IdempotencyRecord(
                            key=idempotency_key,
                            tenant_id=tenant_id,
                            user_id=user_id,
                            result=parsed_result,
                        )
                        if db_rec.expires_at:
                            rec.expires_at = db_rec.expires_at.timestamp()
                        if not rec.is_expired():
                            self.records[comp_key] = rec
                            record = rec
                            if redis_service.is_configured:
                                await redis_service.set(
                                    f"idempotency:{comp_key}",
                                    json.dumps(parsed_result),
                                    ex=settings.IDEMPOTENCY_TTL_SECONDS
                                )
            except Exception as exc:
                logger.debug(f"PostgreSQL idempotency read skipped/failed ({exc})")

        if not record:
            return None

        if record.is_expired():
            if comp_key in self.records:
                del self.records[comp_key]
            return None

        logger.info(f"Idempotency hit for tenant '{tenant_id}' user '{user_id}' key '{idempotency_key}'. Returning cached result.")
        return record.result

    async def save_record(self, user_id: str, idempotency_key: str, result: Dict[str, Any], tenant_id: str = "tenant_default"):
        if not idempotency_key:
            return

        comp_key = self._composite_key(tenant_id, user_id, idempotency_key)
        record = IdempotencyRecord(
            key=idempotency_key,
            tenant_id=tenant_id,
            user_id=user_id,
            result=result,
        )
        self.records[comp_key] = record

        # 1. Save to Redis
        if redis_service.is_configured:
            try:
                await redis_service.set(
                    f"idempotency:{comp_key}",
                    json.dumps(result),
                    ex=settings.IDEMPOTENCY_TTL_SECONDS
                )
            except Exception as exc:
                logger.debug(f"Redis idempotency save skipped ({exc})")

        # 2. Save to PostgreSQL database
        try:
            from app.db.session import async_session_factory
            from app.db.models import IdempotencyRecordModel
            async with async_session_factory() as session:
                db_model = IdempotencyRecordModel(
                    key_hash=comp_key,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    idempotency_key=idempotency_key,
                    response_json=json.dumps(result),
                    expires_at=datetime.fromtimestamp(record.expires_at, tz=timezone.utc),
                )
                session.add(db_model)
                await session.commit()
        except Exception as exc:
            logger.debug(f"PostgreSQL idempotency save skipped/failed ({exc})")


idempotency_manager = IdempotencyManager()
