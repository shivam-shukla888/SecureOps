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
    PRIMARY_API_KEY: str = ""
    PRIMARY_MODEL: str = "gpt-4o-mini"
    PRIMARY_BASE_URL: str = "https://api.openai.com/v1"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"

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

    # Upstash Redis REST Configuration
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""

    # CORS Configuration
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    CORS_ORIGIN_REGEX: str = r"^https://([a-zA-Z0-9_-]+\.)*(vercel\.app|onrender\.com)$"

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ALLOWED_ORIGINS:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def is_upstash_configured(self) -> bool:
        url = self.UPSTASH_REDIS_REST_URL.strip("\"' \t\r\n")
        token = self.UPSTASH_REDIS_REST_TOKEN.strip("\"' \t\r\n")
        return bool(url and token)

    @property
    def has_remote_redis(self) -> bool:
        url = self.REDIS_URL.strip("\"' \t\r\n")
        return bool(url and url != "redis://localhost:6379/0")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()


DANGEROUS_DUMMY_KEYS = {
    "test-secret-api-key-12345",
    "your-secure-bearer-api-key-here",
    "sk-c0b078f9cca6d3da-3af242-0bb15fcc",
    "change-me",
}

DANGEROUS_HMAC_SECRETS = {
    "test-hmac-secret-key-12345",
    "your-hmac-sha256-secret-key-here",
    "secureops-n8n-hmac-secret-key-change-me",
}


def validate_production_config():
    """
    Validates dangerous security settings on application startup.
    Fails startup if critical settings are unsafe or missing in production environment.
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

        # Check API_KEY
        if not settings.API_KEY or settings.API_KEY in DANGEROUS_DUMMY_KEYS:
            raise RuntimeError("Production Configuration Error: API_KEY is missing or using unsafe default placeholder in production.")

        # Check DATABASE_URL
        if not settings.DATABASE_URL or settings.DATABASE_URL == "postgresql+asyncpg://postgres:postgres@localhost:5432/secureops":
            raise RuntimeError("Production Configuration Error: Remote DATABASE_URL is missing or using localhost placeholder in production.")

        # Check Redis (Upstash REST or remote REDIS_URL required in production)
        if not (settings.is_upstash_configured or settings.has_remote_redis):
            raise RuntimeError("Production Configuration Error: Production Redis configuration is missing. Configure UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN or a remote REDIS_URL in production.")

        # Check AI Provider Keys (at least Gemini or Groq must be configured for AI provider operations)
        has_gemini = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in DANGEROUS_DUMMY_KEYS)
        has_groq = bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY not in DANGEROUS_DUMMY_KEYS)
        has_primary = bool(settings.PRIMARY_API_KEY and settings.PRIMARY_API_KEY not in DANGEROUS_DUMMY_KEYS)
        if not (has_gemini or has_groq or has_primary):
            raise RuntimeError("Production Configuration Error: Required AI provider credentials (GEMINI_API_KEY, GROQ_API_KEY, or PRIMARY_API_KEY) are missing in production.")

        # Check N8N_WEBHOOK_SECRET if approval webhook is defined
        if settings.N8N_APPROVAL_WEBHOOK_URL:
            if not settings.N8N_WEBHOOK_SECRET or settings.N8N_WEBHOOK_SECRET in DANGEROUS_HMAC_SECRETS:
                raise RuntimeError("Production Configuration Error: N8N_WEBHOOK_SECRET is missing or using unsafe placeholder in production.")

        logger.info("Production security configuration validation passed successfully.")
