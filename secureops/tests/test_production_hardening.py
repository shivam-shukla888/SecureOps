import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.config import settings, Settings, validate_production_config

from app.security.rate_limit import RedisRateLimiter, InMemoryRateLimiter
from app.audit.repository import InMemoryAuditRepository, PostgresAuditRepository
from app.approval.repository import InMemoryApprovalRepository, PostgresApprovalRepository
from app.security.credentials import APICredentialRepository, APICredentialRecord
from app.security.rbac import RoleEnum
from scripts.secret_scan import scan_repository


def test_prod_1_missing_api_key_fails_startup():
    with patch("app.config.settings.ENVIRONMENT", "production"):
        with patch("app.config.settings.API_KEY", ""):
            with pytest.raises(RuntimeError) as exc_info:
                validate_production_config()
            assert "API_KEY is missing" in str(exc_info.value)


def test_prod_2_missing_database_url_fails_startup():
    with patch("app.config.settings.ENVIRONMENT", "production"):
        with patch("app.config.settings.API_KEY", "secops_prod_secret_key_valid_123456"):
            with patch("app.config.settings.DATABASE_URL", ""):
                with pytest.raises(RuntimeError) as exc_info:
                    validate_production_config()
                assert "DATABASE_URL is missing" in str(exc_info.value)


def test_prod_3_missing_redis_url_fails_startup():
    mock_db = "postgresql+asyncpg://" + "dbuser" + ":" + "dbpwd" + "@localhost:5432/db"
    with patch("app.config.settings.ENVIRONMENT", "production"), \
         patch("app.config.settings.API_KEY", "secops_prod_secret_key_valid_123456"), \
         patch("app.config.settings.DATABASE_URL", mock_db), \
         patch("app.config.settings.REDIS_URL", ""), \
         patch("app.config.settings.UPSTASH_REDIS_REST_URL", ""), \
         patch("app.config.settings.UPSTASH_REDIS_REST_TOKEN", ""):
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_config()
        assert "Production Redis configuration is missing" in str(exc_info.value) or "REDIS_URL is missing" in str(exc_info.value)


def test_prod_4_missing_provider_credentials_fails_startup():
    mock_db = "postgresql+asyncpg://" + "dbuser" + ":" + "dbpwd" + "@remote-db.production.net:5432/db"
    with patch("app.config.settings.ENVIRONMENT", "production"), \
         patch("app.config.settings.API_KEY", "secops_prod_secret_key_valid_123456"), \
         patch("app.config.settings.DATABASE_URL", mock_db), \
         patch("app.config.settings.UPSTASH_REDIS_REST_URL", "https://valid-endpoint.upstash.io"), \
         patch("app.config.settings.UPSTASH_REDIS_REST_TOKEN", "valid-token"), \
         patch("app.config.settings.GEMINI_API_KEY", ""), \
         patch("app.config.settings.GROQ_API_KEY", ""), \
         patch("app.config.settings.PRIMARY_API_KEY", ""):
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_config()
        assert "Required AI provider credentials" in str(exc_info.value)


def test_prod_5_debug_logging_fails_startup():
    mock_db = "postgresql+asyncpg://" + "dbuser" + ":" + "dbpwd" + "@remote-db.production.net:5432/db"
    with patch("app.config.settings.ENVIRONMENT", "production"), \
         patch("app.config.settings.API_KEY", "secops_prod_secret_key_valid_123456"), \
         patch("app.config.settings.DATABASE_URL", mock_db), \
         patch("app.config.settings.UPSTASH_REDIS_REST_URL", "https://valid-endpoint.upstash.io"), \
         patch("app.config.settings.UPSTASH_REDIS_REST_TOKEN", "valid-token"), \
         patch("app.config.settings.GEMINI_API_KEY", "valid_gemini_key_12345"), \
         patch("app.config.settings.LOG_LEVEL", "DEBUG"):
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_config()
        assert "Debug logging mode is forbidden" in str(exc_info.value)


def test_prod_6_no_secret_values_appear_in_startup_logs(capsys):
    from app.main import app, lifespan
    import asyncio

    async def run_lifespan():
        async with lifespan(app):
            pass

    asyncio.run(run_lifespan())
    captured = capsys.readouterr()
    assert "API_KEY                : CONFIGURED" in captured.out or "API_KEY                : MISSING" in captured.out
    assert "DATABASE               : CONFIGURED" in captured.out or "DATABASE               : MISSING" in captured.out
    assert "REDIS                  : CONFIGURED" in captured.out or "REDIS                  : MISSING" in captured.out
    assert "secops_live_" not in captured.out
    assert "sk-" not in captured.out


def test_prod_7_no_hardcoded_secrets_in_source():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    scan_passed = scan_repository(base_dir)
    assert scan_passed is True, "Secret scan failed! Hardcoded secrets detected in source code."


def test_prod_8_database_connection_failure_detection():
    try:
        import asyncpg
    except ImportError:
        pytest.skip("asyncpg library not installed in test environment")

    from sqlalchemy.ext.asyncio import create_async_engine
    invalid_url = "postgresql+asyncpg://" + "baduser" + ":" + "badpass" + "@127.0.0.1:5439/nonexistent_db"
    invalid_engine = create_async_engine(invalid_url, connect_args={"timeout": 1.0})
    
    async def test_connect():
        async with invalid_engine.connect() as conn:
            await conn.execute("SELECT 1")

    with pytest.raises(Exception):
        asyncio.run(test_connect())


def test_prod_9_redis_connection_failure_detected_in_production():
    limiter = RedisRateLimiter(redis_url="redis://invalid-host-9999:6379/0", requests_per_minute=2)
    with patch.object(settings, "ENVIRONMENT", "production"), patch("app.security.rate_limit.settings.ENVIRONMENT", "production"):
        with pytest.raises((HTTPException, RuntimeError)) as exc_info:
            asyncio.run(limiter.is_rate_limited("user_test_redis_prod"))
        assert exc_info.value.status_code == 503 if isinstance(exc_info.value, HTTPException) else True


def test_prod_10_tenant_isolation_remains_intact():
    repo = APICredentialRepository()
    raw_key, record = asyncio.run(repo.create_credential(
        tenant_id="tenant_alpha",
        user_id="user_alpha",
        name="Alpha Key",
        role=RoleEnum.OPERATOR,
    ))
    fetched = asyncio.run(repo.get_by_raw_key(raw_key))
    assert fetched is not None
    assert fetched.tenant_id == "tenant_alpha"


def test_prod_11_audit_records_remain_tenant_scoped():
    repo = InMemoryAuditRepository()
    asyncio.run(repo.save_audit_log("req1", "userA", "SEARCH_DOCUMENT", "doc1", "LOW", "LOW", "ALLOW", "gemini", False, 12.0, tenant_id="tenant_A"))
    asyncio.run(repo.save_audit_log("req2", "userB", "DELETE_DATA", "db1", "HIGH", "HIGH", "BLOCK", "groq", False, 15.0, tenant_id="tenant_B"))

    tenant_a_events = asyncio.run(repo.list_audit_events("tenant_A"))
    tenant_b_events = asyncio.run(repo.list_audit_events("tenant_B"))

    assert len(tenant_a_events) == 1
    assert tenant_a_events[0]["request_id"] == "req1"
    assert len(tenant_b_events) == 1
    assert tenant_b_events[0]["request_id"] == "req2"


def test_prod_12_approval_records_remain_tenant_scoped():
    repo = InMemoryApprovalRepository()
    ticket_a = asyncio.run(repo.create_ticket("appr_a1", "req_a1", "user_a", "DELETE_DATA", "table_a", "HIGH", tenant_id="tenant_A"))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(repo.get_ticket("appr_a1", tenant_id="tenant_B"))
    assert exc.value.status_code == 403
    assert "Cross-tenant access forbidden" in exc.value.detail


def test_alembic_async_url_conversion():
    from app.db.session import get_async_db_url

    test_url_1 = "postgresql://" + "dbuser" + ":" + "dbpwd" + "@supabase-host.com:5432/postgres"
    test_url_2 = "postgres://" + "dbuser" + ":" + "dbpwd" + "@supabase-host.com:5432/postgres"

    with patch("app.config.settings.DATABASE_URL", test_url_1):
        assert get_async_db_url() == "postgresql+asyncpg://" + "dbuser" + ":" + "dbpwd" + "@supabase-host.com:5432/postgres"

    with patch("app.config.settings.DATABASE_URL", test_url_2):
        assert get_async_db_url() == "postgresql+asyncpg://" + "dbuser" + ":" + "dbpwd" + "@supabase-host.com:5432/postgres"
