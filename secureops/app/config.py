import logging
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Core Application Settings
    API_KEY: str = "test-secret-api-key-12345"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # AI Provider API Keys & Models
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BACKEND: str = "memory"  # "memory" or "redis"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Database Persistence
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/secureops"

    # n8n HITL Webhook & HMAC Security
    N8N_APPROVAL_WEBHOOK_URL: str = "https://alphhha.app.n8n.cloud/webhook/approval-request"
    N8N_WEBHOOK_SECRET: str = "test-hmac-secret-key-12345"
    APPROVAL_EXPIRY_MINUTES: int = 60

    # Request Size & Text Limits
    MAX_REQUEST_SIZE_BYTES: int = 1024 * 1024
    MAX_REQUEST_LENGTH_CHARS: int = 4000

    # Tool Execution & SSRF Security Controls
    ALLOWED_OUTBOUND_HOSTS: List[str] = [
        "api.internal-doc-service.com",
        "alphhha.app.n8n.cloud",
    ]
    EXECUTION_TIMEOUT_SECONDS: float = 10.0
    IDEMPOTENCY_TTL_SECONDS: int = 86400
    MAX_TOOL_INPUT_SIZE: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()


def validate_production_config():
    """
    Validates dangerous security settings on application startup.
    Fails startup if critical settings are unsafe in production environment.
    """
    if settings.ENVIRONMENT.lower() == "production":
        if not settings.ALLOWED_OUTBOUND_HOSTS:
            raise RuntimeError("Production Configuration Error: ALLOWED_OUTBOUND_HOSTS policy cannot be empty in production.")
        if settings.EXECUTION_TIMEOUT_SECONDS <= 0:
            raise RuntimeError("Production Configuration Error: EXECUTION_TIMEOUT_SECONDS must be positive.")
        if settings.IDEMPOTENCY_TTL_SECONDS <= 0:
            raise RuntimeError("Production Configuration Error: IDEMPOTENCY_TTL_SECONDS must be positive.")
        if settings.LOG_LEVEL.upper() == "DEBUG":
            raise RuntimeError("Production Configuration Error: Debug logging mode is forbidden in production environment.")
        logger.info("✅ Production security configuration validation passed successfully.")
