import time
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import HTTPException, status

from app.config import settings
from app.security.redis_service import redis_service, RedisService

logger = logging.getLogger(__name__)


class BaseRateLimiter(ABC):
    @abstractmethod
    async def is_rate_limited(self, identifier: str) -> bool:
        pass

    def reset(self):
        pass


class InMemoryRateLimiter(BaseRateLimiter):
    def __init__(self, requests_per_minute: int = 60, window_seconds: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)

    async def is_rate_limited(self, identifier: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds

        self.requests[identifier] = [
            ts for ts in self.requests[identifier] if ts > cutoff
        ]

        if len(self.requests[identifier]) >= self.requests_per_minute:
            return True

        self.requests[identifier].append(now)
        return False

    def reset(self):
        self.requests.clear()


class RedisRateLimiter(BaseRateLimiter):
    def __init__(
        self,
        requests_per_minute: int = settings.RATE_LIMIT_PER_MINUTE,
        window_seconds: int = 60,
        redis_url: Optional[str] = None,
    ):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.redis_service = RedisService(redis_url=redis_url) if redis_url else redis_service
        self.fallback_limiter = InMemoryRateLimiter(
            requests_per_minute=requests_per_minute,
            window_seconds=window_seconds,
        )

    def reset(self):
        self.fallback_limiter.reset()

    async def is_rate_limited(self, identifier: str) -> bool:
        is_prod = str(getattr(settings, "ENVIRONMENT", "development")).lower() == "production"

        if not self.redis_service.is_configured:
            if is_prod:
                logger.error("Production Error: Rate limiter Redis backend is not configured; failing closed.")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Production Security Control Failure: Rate limiting backend unavailable."
                )
            return await self.fallback_limiter.is_rate_limited(identifier)

        try:
            now = time.time()
            cutoff = now - self.window_seconds
            key = f"ratelimit:{identifier}"

            commands = [
                ["ZREMRANGEBYSCORE", key, "0", str(cutoff)],
                ["ZADD", key, str(now), str(now)],
                ["ZCARD", key],
                ["EXPIRE", key, str(self.window_seconds + 5)],
            ]
            results = await self.redis_service.pipeline_execute(commands)
            request_count = int(results[2]) if (isinstance(results, list) and len(results) >= 3) else 1
            return request_count > self.requests_per_minute
        except HTTPException:
            raise
        except Exception as exc:
            if is_prod:
                logger.error(f"Production Redis rate limiter execution failure ({type(exc).__name__}); failing closed.")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Production Security Control Failure: Rate limiting backend unavailable."
                )
            logger.warning(f"Redis rate limiter error ({exc}); falling back to in-memory in dev.")
            return await self.fallback_limiter.is_rate_limited(identifier)


def get_rate_limiter() -> BaseRateLimiter:
    is_prod = str(getattr(settings, "ENVIRONMENT", "development")).lower() == "production"
    if settings.RATE_LIMIT_BACKEND.lower() == "redis" or settings.is_upstash_configured or is_prod:
        return RedisRateLimiter(
            requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
        )
    return InMemoryRateLimiter(requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)


rate_limiter_instance = get_rate_limiter()
rate_limiter = rate_limiter_instance


async def check_rate_limit(identifier: str):
    if await rate_limiter_instance.is_rate_limited(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {settings.RATE_LIMIT_PER_MINUTE} requests per minute allowed."
        )
