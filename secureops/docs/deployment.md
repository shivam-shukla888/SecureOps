# SecureOps Production Deployment Guide

This guide outlines deployment requirements, environment configurations, Docker setup, and PostgreSQL / Redis integration for running SecureOps in production environments.

---

## 1. Prerequisites & Infrastructure

- **Python**: 3.11+ (or Docker container)
- **PostgreSQL**: 14+ with asyncpg connection support
- **Redis**: 6.2+ (or Upstash Redis for serverless environments)
- **SSL / TLS**: Mandatory termination (HTTPS only)

---

## 2. Environment Configuration (`.env`)

Create a `.env` file from `.env.example`. Never commit `.env` to Git.

```ini
# Application Mode
ENVIRONMENT=production
DEBUG=False

# API Gateway Security
SECOPS_API_KEY=your-secure-production-api-key-min-32-chars
ALLOWED_ORIGINS=["https://dashboard.secureops.internal"]

# PostgreSQL Database (Asyncpg)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db



# Redis / Upstash Cache & Rate Limiting
REDIS_URL=rediss://:YourRedisPassword@redis.internal:6379/0
# Or Upstash REST:
# UPSTASH_REDIS_REST_URL=https://your-upstash-instance.upstash.io
# UPSTASH_REDIS_REST_TOKEN=your-upstash-rest-token

# Outbound Network Allowlist (SSRF Protection)
ALLOWED_OUTBOUND_HOSTS=["api.internal-doc-service.com", "api.openai.com"]

# Secret Management (Optional external secret providers)
SECRET_PROVIDER=env  # Options: env, vault, aws_secrets_manager
```

---

## 3. Database Migrations

Apply Alembic migrations to upgrade database schema to the latest version:

```bash
# Verify migration head
alembic heads

# Apply all migrations to database
alembic upgrade head
```

---

## 4. Docker Deployment

### Building the Container
```bash
docker build -t secureops-gateway:5.0.0 .
```

### Running with Docker Compose
```bash
docker-compose up -d
```

---

## 5. Security & Verification Checklist

- [ ] HTTPS enforced on all incoming traffic.
- [ ] Database credentials loaded strictly via environment/secrets manager.
- [ ] Redis TLS (`rediss://`) enabled for distributed rate limiting.
- [ ] Alembic migration `004_agent_benchmarks` applied.
- [ ] Outbound network allowlist restricted to approved endpoints.
- [ ] Secret scanner executed prior to deployment (`python scripts/secret_scan.py`).
