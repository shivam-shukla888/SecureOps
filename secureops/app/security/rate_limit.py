import time
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)


class BaseRateLimiter(ABC):
    @abstractmethod
    async def is_rate_limited(self, identifier: str) -> bool:
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
        redis_url: str = settings.REDIS_URL,
        requests_per_minute: int = settings.RATE_LIMIT_PER_MINUTE,
        window_seconds: int = 60,
    ):
        self.redis_url = redis_url
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.fallback_limiter = InMemoryRateLimiter(
            requests_per_minute=requests_per_minute,
            window_seconds=window_seconds,
        )
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(self.redis_url, socket_timeout=2.0)
            except Exception as exc:
                logger.warning(f"Failed to connect to Redis ({exc}); falling back to in-memory rate limiter.")
                return None
        return self._redis

    async def is_rate_limited(self, identifier: str) -> bool:
        try:
            r = await self._get_redis()
            if r is None:
                return await self.fallback_limiter.is_rate_limited(identifier)

            now = time.time()
            key = f"ratelimit:{identifier}"
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, now - self.window_seconds)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self.window_seconds + 5)
            results = await pipe.execute()

            request_count = results[2]
            return request_count > self.requests_per_minute
        except Exception as exc:
            logger.warning(f"Redis rate limiter error ({exc}); failing safe to in-memory rate limiter.")
            return await self.fallback_limiter.is_rate_limited(identifier)


def get_rate_limiter() -> BaseRateLimiter:
    if settings.RATE_LIMIT_BACKEND.lower() == "redis":
        return RedisRateLimiter(
            redis_url=settings.REDIS_URL,
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
