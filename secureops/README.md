# SecureOps — Backend Engine & Adversarial Benchmark Core

SecureOps is a production-grade **Universal AI Agent Security Gateway, Tool Execution Firewall & Adversarial Benchmark Engine** built with Python, FastAPI, async SQLAlchemy, PostgreSQL, and Redis.

---

## Core Security Pipeline

```text
Client / External Agent (Bearer Key)
  ↓
Hashed API Credential Authentication & Server-Side Tenant Context (TenantUserContext)
  ↓
Input Validation & Size Guard (Payload Cap: 1MB, Character Limit: 4000)
  ↓
AI Provider Classification Chain (Gemini 2.5 Flash -> Groq Fallback -> Fail-Closed)
  ↓
Deterministic Policy Engine (Canonical Risk Matrix & Anti-Downgrade Enforcement)
  ↓
Human-In-The-Loop Approval Engine (Time-bound Single-Use Tickets & HMAC Webhooks)
  ↓
Tool Security Gateway (Allowlist Verification, Regex Shell Escape, Path Traversal & SSRF Filters)
  ↓
Secure Execution Engine (Tenant Data Isolation, Timeout Control, Secret Masking)
  ↓
SIEM & Audit Logging (PostgreSQL asyncpg Persistence, Redacted JSON Log, Console/Webhook Exporters)
```

---

## Capabilities & Subsystems

1. **Universal Agent Adapters (`app/adapters/`)**:
   - `OpenAICompatibleAgentAdapter`: Connects OpenAI, Groq, vLLM, LocalAI, Ollama, and Mistral agents with dynamic secret management and safe mocked fallback.
   - `GenericHTTPAgentAdapter`: Connects internal enterprise REST agents (LangChain, CrewAI, AutoGen) with SSRF checks, open redirect blocking (`follow_redirects=False`), and 2MB response caps.
   - `SimulatedAgentAdapter`: Offline sandbox simulator for safe deterministic test runs.
2. **Standard Adversarial Benchmark Engine (`security-baseline-v1`)**:
   - 20 baseline security scenarios across 6 categories (Prompt Injection, Jailbreak, Tool Abuse, Data Exfiltration, Network SSRF, Command Injection, Privilege Escalation).
   - **Adaptive Testing Loop**: Feedback mechanism executing targeted multi-stage attack variants (`PI-002`, `MA-002`, `SSRF-002`, `PE-002`) bounded to `MAX_ADAPTIVE_REQUESTS = 10`.
3. **Multi-Tenancy & Tenant Data Isolation**: All persisted models (`agents`, `agent_evaluations`, `agent_benchmarks`, `benchmark_findings`, `audit_logs`, `approval_tickets`, `idempotency_records`) are strictly partitioned by `tenant_id`.
4. **Role-Based Access Control (RBAC)**: Server-side authorization enforcing 5 roles (`OWNER`, `ADMIN`, `APPROVER`, `OPERATOR`, `VIEWER`).
5. **Hashed Credential Management**: API keys are securely hashed (`SHA-256`) and never stored in plaintext.
6. **PostgreSQL Migrations (Alembic)**: Revisions `001_initial_tables` $\rightarrow$ `002_production_tables` $\rightarrow$ `003_agent_security_gateway` $\rightarrow$ `004_agent_benchmarks` (`head`).

---

## Directory Structure

```text
secureops/
├── alembic/                 # Alembic migration scripts (001 -> 004 head)
├── app/
│   ├── main.py              # FastAPI app & endpoints
│   ├── config.py            # Startup security configuration validator
│   ├── adapters/            # Universal Agent Adapters (OpenAI, HTTP, Simulated)
│   ├── routes/              # Agent Registry, Evaluations & Benchmark Routers
│   ├── schemas/             # Request, Decision, Approval, Execution, Agent Schemas
│   ├── security/            # Policy Engine, Tool Gateway, Auth, RBAC, SSRF, Rate Limit
│   │   └── benchmarks/      # Adversarial Benchmark Engine & Scorecard
│   ├── ai/                  # AI Providers (Gemini, Groq) & Classifier
│   ├── approval/            # HITL Approval Ticket Manager
│   ├── audit/               # Audit Logger, Metrics & SIEM Exporters
│   ├── db/                  # PostgreSQL Models & Async Session Factory
│   └── executor/            # Tool Dispatcher & Safe Sandbox
├── docs/                    # Architecture, Integration & Benchmark Documentation
├── scripts/
│   ├── demo_universal_agent.py # End-to-end agent evaluation demo script
│   └── secret_scan.py       # Hardcoded secret scanner
└── tests/                   # 147+ Automated Pytest Security & Regression Tests
```

---

## Verification & Execution Commands

### 1. Run Automated Test Suite (147+ Tests)

```bash
cd secureops
python -m pytest -v
```

### 2. Run Hardcoded Secret Scan

```bash
python scripts/secret_scan.py
```

### 3. Run Universal Agent Benchmark Demo

```bash
python scripts/demo_universal_agent.py
```

### 4. Start Development Gateway Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
