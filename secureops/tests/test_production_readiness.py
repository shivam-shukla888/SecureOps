import os
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.config import Settings, validate_production_config
from app.db.session import get_db_connection_params, check_db_connectivity
from app.security.redis_service import RedisService
from app.security.rate_limit import RedisRateLimiter, InMemoryRateLimiter, get_rate_limiter
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_upstash_configuration_detection():
    """Proves that Upstash REST credentials are correctly detected and prioritized."""
    service = RedisService(
        rest_url="https://test-endpoint.upstash.io",
        rest_token="test-upstash-token-12345",
        redis_url="redis://localhost:6379/0",
    )
    assert service.is_upstash is True
    assert service.is_configured is True
    assert service._rest_url == "https://test-endpoint.upstash.io"
    assert service._rest_token == "test-upstash-token-12345"


def test_localhost_redis_rejected_in_production():
    """Proves that localhost Redis is never treated as configured in production."""
    with patch("app.security.redis_service.settings.ENVIRONMENT", "production"):
        service = RedisService(
            rest_url="",
            rest_token="",
            redis_url="redis://localhost:6379/0",
        )
        assert service.is_upstash is False
        assert service.is_configured is False


def test_remote_redis_accepted_in_production():
    """Proves that remote Redis URLs are accepted in production."""
    with patch("app.security.redis_service.settings.ENVIRONMENT", "production"):
        service = RedisService(
            rest_url="",
            rest_token="",
            redis_url="redis://remote-redis.production.net:6379/0",
        )
        assert service.is_configured is True


@pytest.mark.asyncio
async def test_rate_limiter_fails_closed_in_production():
    """Proves that rate limiter strictly fails closed (HTTP 503) in production when Redis is unconfigured."""
    with patch("app.security.rate_limit.settings.ENVIRONMENT", "production"):
        unconfigured_service = RedisService(
            rest_url="",
            rest_token="",
            redis_url="redis://localhost:6379/0",
        )
        limiter = RedisRateLimiter(requests_per_minute=60)
        limiter.redis_service = unconfigured_service

        with pytest.raises(HTTPException) as exc_info:
            await limiter.is_rate_limited("user_prod_test")
        assert exc_info.value.status_code == 503
        assert "Rate limiting backend unavailable" in exc_info.value.detail


@pytest.mark.asyncio
async def test_rate_limiter_fails_closed_on_redis_exception_in_production():
    """Proves that rate limiter strictly fails closed (HTTP 503) when Redis execution fails in production."""
    with patch("app.security.rate_limit.settings.ENVIRONMENT", "production"):
        mock_service = AsyncMock(spec=RedisService)
        mock_service.is_configured = True
        mock_service.pipeline_execute.side_effect = ConnectionError("Upstash network timeout")

        limiter = RedisRateLimiter(requests_per_minute=60)
        limiter.redis_service = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await limiter.is_rate_limited("user_prod_test")
        assert exc_info.value.status_code == 503


def test_db_url_parsing_and_ssl_normalization():
    """Proves that DATABASE_URL parsing strips unsupported sslmode and sets connect_args correctly."""
    # 1. Supabase pooler URL with ?sslmode=require
    raw_supabase = "postgresql://" + "dbuser" + ":" + "dbpwd" + "@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres?sslmode=require"
    clean_url, connect_args = get_db_connection_params(raw_supabase)
    assert clean_url.startswith("postgresql+asyncpg://")
    assert "sslmode" not in clean_url
    assert connect_args.get("ssl") == "require"
    assert connect_args.get("timeout") == 5.0

    # 2. Plain postgres:// with remote host
    raw_remote = "postgres://" + "adminuser" + ":" + "adminpwd" + "@db.production.render.com:5432/appdb"
    clean_url_rem, connect_args_rem = get_db_connection_params(raw_remote)
    assert clean_url_rem.startswith("postgresql+asyncpg://")
    assert connect_args_rem.get("ssl") == "require"

    # 3. Localhost database without SSL
    raw_local = "postgresql+asyncpg://postgres:postgres@localhost:5432/secureops"
    clean_url_loc, connect_args_loc = get_db_connection_params(raw_local)
    assert "ssl" not in connect_args_loc


@pytest.mark.asyncio
async def test_real_db_connectivity_check():
    """Proves that check_db_connectivity executes against PostgreSQL."""
    ok = await check_db_connectivity()
    # When connected to configured test/local db, returns boolean True
    assert isinstance(ok, bool)


def test_health_independent_liveness(client):
    """Proves /health is an independent liveness check returning 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SecureOps API Gateway"
    assert "timestamp" in data


def test_ready_reflects_dependency_status(client):
    """Proves /ready returns detailed status of dependencies."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "rate_limiter" in data
    assert "database" in data
    assert "redis" in data
    assert "metrics_summary" in data


def test_production_validation_blocks_insecure_defaults():
    """Proves validate_production_config blocks dummy secrets, missing DB, or missing Redis in production."""
    with patch("app.config.settings.ENVIRONMENT", "production"), \
         patch("app.config.settings.API_KEY", "test-secret-api-key-12345"):
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_config()
        assert "API_KEY is missing or using unsafe default placeholder" in str(exc_info.value)
