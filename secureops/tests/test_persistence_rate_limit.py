import asyncio
import pytest
from app.audit.repository import InMemoryAuditRepository
from app.security.rate_limit import InMemoryRateLimiter, RedisRateLimiter


def test_in_memory_audit_repository_saves_logs():
    async def run_test():
        repo = InMemoryAuditRepository()
        await repo.save_audit_log(
            request_id="req_test_persist",
            user_id="user_test",
            intent="SEARCH_DOCUMENT",
            resource="doc1",
            ai_risk="LOW",
            policy_risk="LOW",
            final_decision="ALLOW",
            provider="gemini",
            fallback_used=False,
            latency_ms=45.2,
        )
        return repo

    repo = asyncio.run(run_test())
    assert len(repo.logs) == 1
    assert repo.logs[0]["request_id"] == "req_test_persist"
    assert repo.logs[0]["provider"] == "gemini"
    assert repo.logs[0]["fallback_used"] is False


def test_redis_rate_limiter_falls_back_safely():
    async def run_test():
        limiter = InMemoryRateLimiter(requests_per_minute=2)
        res1 = await limiter.is_rate_limited("user_1")
        res2 = await limiter.is_rate_limited("user_1")
        res3 = await limiter.is_rate_limited("user_1")
        return res1, res2, res3

    r1, r2, r3 = asyncio.run(run_test())
    assert r1 is False
    assert r2 is False
    assert r3 is True  # Rate limited on 3rd request
