import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.config import settings, Settings
from app.security.redis_service import RedisService
from app.security.rate_limit import RedisRateLimiter, InMemoryRateLimiter


def test_1_missing_redis_configuration():
    """Verify RedisService behaves safely when unconfigured."""
    async def _test():
        service = RedisService(rest_url="", rest_token="", redis_url="")
        assert service.is_configured is False
        assert await service.ping() is False
        assert await service.get("key") is None
    asyncio.run(_test())


def test_2_redis_configuration_loading():
    """Verify Upstash configuration properties on Settings."""
    cfg = Settings(
        UPSTASH_REDIS_REST_URL="https://test.upstash.io",
        UPSTASH_REDIS_REST_TOKEN="test_token_123"
    )
    assert cfg.is_upstash_configured is True
    assert cfg.UPSTASH_REDIS_REST_URL == "https://test.upstash.io"


def test_3_redis_client_initialization():
    """Verify HTTP client header initialization in RedisService."""
    async def _test():
        service = RedisService(rest_url="https://test.upstash.io", rest_token="my_token")
        client = service._get_http_client()
        assert client.headers["Authorization"] == "Bearer my_token"
        await service.close()
    asyncio.run(_test())


def test_4_redis_ping_success():
    """Verify ping returns True on PONG response."""
    async def _test():
        service = RedisService(rest_url="https://test.upstash.io", rest_token="my_token")
        with patch.object(service, "_execute_upstash_cmd", new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = "PONG"
            assert await service.ping() is True
            mock_cmd.assert_called_once_with(["PING"])
        await service.close()
    asyncio.run(_test())


def test_5_set_get_operations():
    """Verify set and get operations formatting."""
    async def _test():
        service = RedisService(rest_url="https://test.upstash.io", rest_token="my_token")
        with patch.object(service, "_execute_upstash_cmd", new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = "OK"
            assert await service.set("foo", "bar", ex=60) is True
            mock_cmd.assert_called_with(["SET", "foo", "bar", "EX", "60"])

            mock_cmd.return_value = "bar"
            assert await service.get("foo") == "bar"
            mock_cmd.assert_called_with(["GET", "foo"])
        await service.close()
    asyncio.run(_test())


def test_6_expiration_ttl():
    """Verify expire operation formatting."""
    async def _test():
        service = RedisService(rest_url="https://test.upstash.io", rest_token="my_token")
        with patch.object(service, "_execute_upstash_cmd", new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = 1
            assert await service.expire("foo", 30) is True
            mock_cmd.assert_called_with(["EXPIRE", "foo", "30"])
        await service.close()
    asyncio.run(_test())


def test_7_atomic_increment():
    """Verify incr operation."""
    async def _test():
        service = RedisService(rest_url="https://test.upstash.io", rest_token="my_token")
        with patch.object(service, "_execute_upstash_cmd", new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = 5
            res = await service.incr("counter", amount=1)
            assert res == 5
            mock_cmd.assert_called_with(["INCR", "counter"])
        await service.close()
    asyncio.run(_test())


from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock

def test_8_redis_failure_behavior_dev_vs_prod():
    """Verify dev fallback vs production fail-closed behavior on Redis failure."""
    async def _test():
        limiter = RedisRateLimiter(requests_per_minute=2)

        with patch("app.config.settings.ENVIRONMENT", "development"):
            with patch.object(RedisService, "is_configured", new_callable=PropertyMock, return_value=True):
                with patch("app.security.redis_service.redis_service.pipeline_execute", side_effect=Exception("Redis connection error")):
                    res = await limiter.is_rate_limited("dev_user")
                    assert res is False

        with patch("app.config.settings.ENVIRONMENT", "production"):
            with patch.object(RedisService, "is_configured", new_callable=PropertyMock, return_value=True):
                with patch("app.security.redis_service.redis_service.pipeline_execute", side_effect=Exception("Redis connection error")):
                    with pytest.raises(HTTPException) as exc_info:
                        await limiter.is_rate_limited("prod_user")
                    assert exc_info.value.status_code == 503
    asyncio.run(_test())


def test_9_rate_limiting_with_redis_pipeline():
    """Verify RedisRateLimiter uses sliding window pipeline execution."""
    async def _test():
        limiter = RedisRateLimiter(requests_per_minute=2)
        with patch.object(RedisService, "is_configured", new_callable=PropertyMock, return_value=True):
            with patch("app.security.redis_service.redis_service.pipeline_execute", new_callable=AsyncMock) as mock_pipe:
                mock_pipe.return_value = [0, 1, 3, 1]  # 3 requests > 2 allowed -> rate limited!
                is_limited = await limiter.is_rate_limited("user_123")
                assert is_limited is True
    asyncio.run(_test())


def test_10_tenant_isolation_in_rate_limiting():
    """Verify tenant context is isolated in Redis rate limiting keys."""
    async def _test():
        limiter = RedisRateLimiter(requests_per_minute=5)
        with patch.object(RedisService, "is_configured", new_callable=PropertyMock, return_value=True):
            with patch("app.security.redis_service.redis_service.pipeline_execute", new_callable=AsyncMock) as mock_pipe:
                mock_pipe.return_value = [0, 1, 1, 1]
                await limiter.is_rate_limited("tenant_A:user_1")
                call_args = mock_pipe.call_args[0][0]
                assert call_args[0][1] == "ratelimit:tenant_A:user_1"
    asyncio.run(_test())
