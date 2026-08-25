import asyncio
import pytest
from app.security.rate_limit import RedisRateLimiter, InMemoryRateLimiter


def test_redis_rate_limiter_graceful_fallback_when_unavailable():
    async def run_test():
        limiter = RedisRateLimiter(
            redis_url="redis://invalid-redis-server-host:6379/0",
            requests_per_minute=2,
        )
        res1 = await limiter.is_rate_limited("user_test_redis_1")
        res2 = await limiter.is_rate_limited("user_test_redis_1")
        res3 = await limiter.is_rate_limited("user_test_redis_1")
        return res1, res2, res3

    r1, r2, r3 = asyncio.run(run_test())
    assert r1 is False
    assert r2 is False
    assert r3 is True  # Rate limited on 3rd request via graceful fallback to memory
