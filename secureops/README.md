# SecureOps Enterprise AI Gateway & Security Control Layer (Phase 5)

SecureOps is a production-grade Enterprise AI Request Gateway, Multi-Provider Fallback System, Deterministic Security Policy Engine, Multi-Tenant Control Plane, and Secure Tool Executor built with Python and FastAPI.

---

## Architecture & Security Pipeline

```text
Client / Agent (Bearer Key)
  ↓
Hashed API Credential Authentication & Tenant Context (tenant_id, user_id, role)
  ↓
Input Validation & Size Guard (Payload Limit, Character Limit, Parameter Stripping)
  ↓
AI Provider Chain (Gemini 2.5 Flash -> Groq Fallback)
  ↓
Deterministic Policy Engine (Canonical Risk Matrix & Anti-Downgrade Rules)
  ↓
Human-In-The-Loop Approval Engine (Time-bound Tickets & Self-Approval Prevention)
  ↓
Tool Permission Engine & Server-Side Allowlist Validation
  ↓
Secure Execution Engine (Tenant Data Isolation, SSRF Guard, Secret Isolation, Timeout Control)
  ↓
SIEM & Audit Logging (Redacted JSON, PostgreSQL Persistence, Console/Webhook Exporters)
```

---

## Phase 5 Core Features

1. **Multi-Tenancy & Tenant Data Isolation**: All persisted state (`audit_logs`, `approval_tickets`, `execution_records`, `idempotency_records`) is strictly partitioned by `tenant_id`. Cross-tenant access is blocked with `HTTP 403 Forbidden`.
2. **Role-Based Access Control (RBAC)**: Server-side authorization enforcing 5 roles (`OWNER`, `ADMIN`, `APPROVER`, `OPERATOR`, `VIEWER`). Users cannot self-assign privileges.
3. **Hashed Credential Management**: API keys are securely hashed (`SHA-256`). Supports tenant-scoped credential creation, key rotation, and instant revocation.
4. **Real Safe Tool Integration**: Safe read-only `DocumentServiceAdapter` for tenant-isolated document searches.
5. **SIEM Exporters & Security Events**: Dedicated security event pipeline (`AUTH_FAILURE`, `PROMPT_INJECTION`, `SSRF_BLOCK`, etc.) with asynchronous `ConsoleSIEMExporter` and `WebhookSIEMExporter` adapters.
6. **Tenant Dashboard & Governance APIs**: Endpoints `GET /v1/approvals`, `GET /v1/audit/events`, and `GET /v1/dashboard/summary` providing real-time tenant metrics.

---

## Directory Structure

```
secureops/
├── app/
│   ├── main.py              # FastAPI app & endpoints (/v1/requests, /v1/executions, /v1/approvals, /v1/audit, /v1/dashboard, /v1/credentials)
│   ├── config.py            # Startup security configuration validator
│   ├── schemas/
│   │   ├── request.py       # Input validation & forbidden parameter stripping
│   │   ├── decision.py      # Classification & gateway response schemas
│   │   ├── approval.py      # HITL approval request & result schemas
│   │   ├── execution.py     # Tool execution request & response schemas
│   │   └── credential.py    # Credential management schemas
│   ├── security/
│   │   ├── auth.py          # Hashed Bearer token validation & tenant context attachment
│   │   ├── rbac.py          # RoleEnum & server-side require_role dependency
│   │   ├── credentials.py   # APICredentialRepository (hashing, rotation, revocation)
│   │   ├── validation.py    # Size limits (413) & text length checks
│   │   ├── policy.py        # Deterministic policy engine & anti-downgrade rules
│   │   ├── rate_limit.py    # Memory & Redis sliding-window rate limiters (429)
│   │   ├── hmac.py          # HMAC-SHA256 signature verification & timestamp replay protection
│   │   ├── secrets.py       # SecretProvider isolation with key allowlist
│   │   ├── network.py       # SSRF protection & outbound host allowlist
│   │   ├── idempotency.py   # Idempotency-Key caching manager (tenant-scoped)
│   │   └── headers.py       # Security headers middleware (HSTS, Nosniff, Frame Options)
│   ├── ai/
│   │   ├── classifier.py    # Gemini -> Groq fallback classifier orchestrator
│   │   ├── prompts.py       # System prompt for untrusted input classification
│   │   └── providers/
│   │       ├── base.py      # Abstract AI provider interface
│   │       ├── gemini.py    # Gemini 2.5 Flash provider
│   │       └── groq.py      # Groq Llama-3.3-70b provider
│   ├── tools/
│   │   ├── base.py          # ToolDefinition dataclass
│   │   ├── schemas.py       # Pydantic tool input schemas (extra="forbid", injection checks)
│   │   ├── registry.py      # Deterministic ToolRegistry mapping
│   │   ├── permissions.py   # Server-side tool permission engine & ticket binding
│   │   └── integrations/
│   │       └── document_service.py # Real safe read-only DocumentServiceAdapter
│   ├── db/
│   │   ├── session.py       # Async SQLAlchemy engine
│   │   ├── models.py        # AuditLogModel and ApprovalTicketModel
│   │   └── safe_query.py    # SafeDatabaseQueryAdapter (parameterized SQL & tenant scoping)
│   ├── approval/
│   │   ├── repository.py    # Multi-tenant approval ticket repository
│   │   └── manager.py       # HITL approval manager & self-approval prevention
│   ├── audit/
│   │   ├── logger.py        # Redacted JSON logger
│   │   ├── repository.py    # Multi-tenant audit repository
│   │   ├── metrics.py       # Application metrics tracker
│   │   ├── security_events.py # SecurityEvent model & security event types
│   │   └── siem.py          # Console & Webhook SIEM exporters
│   ├── n8n/
│   │   └── webhook.py       # Outbound HMAC-signed n8n notification client
│   └── executor/
│       └── dispatcher.py    # Tool execution dispatcher with timeout control
├── scripts/
│   ├── secret_scan.py       # Repository secret scanner script
│   ├── demo.py              # Scenario demo script
│   ├── e2e_demo.py          # Real end-to-end 7-scenario validation script
│   └── benchmark.py         # Micro-benchmark script
├── tests/                   # 88-test regression suite covering all security controls
│   ├── conftest.py
│   ├── test_adversarial.py  # 19 automated attack case tests
│   ├── test_phase5_multitenancy_rbac.py # Multi-tenancy, RBAC, & credential tests
│   ├── test_api.py
│   ├── test_approval_binding.py
│   ├── test_approvals.py
│   ├── test_auth.py
│   ├── test_fallback.py
│   ├── test_hmac_replay.py
│   ├── test_idempotency_and_timeout.py
│   ├── test_input_sanitization.py
│   ├── test_persistence_rate_limit.py
│   ├── test_policy.py
│   ├── test_prompt_injection.py
│   ├── test_redis_integration.py
│   ├── test_ssrf_and_secrets.py
│   ├── test_tool_permissions.py
│   └── test_validation.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
├── PRODUCT.md
├── DEMO.md
├── PERFORMANCE.md
├── ARCHITECTURE.md
├── SECURITY.md
└── SECURITY_SCORECARD.md
```

---

## Quickstart & Commands

### 1. Run Automated Test Suite (88 Tests)

```bash
cd secureops
python -m pytest -v
```

### 2. Run Secret Scan

```bash
python scripts/secret_scan.py
```

### 3. Run E2E Production Demo

```bash
python scripts/e2e_demo.py
```

### 4. Run Micro-Benchmark

```bash
python scripts/benchmark.py
```

### 5. Launch Local Docker Compose Environment

```bash
cd ..
docker-compose up --build
```
