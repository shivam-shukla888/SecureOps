# SecureOps — Universal AI Agent Security Gateway & Adversarial Benchmark Engine

[![Vercel Deployment](https://img.shields.io/badge/Vercel-Live%20Dashboard-black.svg?logo=vercel)](https://secure-ops-pi.vercel.app)
[![Render Gateway](https://img.shields.io/badge/Render-API%20Gateway-46E3B7.svg?logo=render)](https://secureops-gateway.onrender.com)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-emerald.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-cyan.svg?logo=react)](https://react.dev/)
[![Vitest](https://img.shields.io/badge/Vitest-39%20Passed-brightgreen.svg?logo=vitest)]()
[![Pytest](https://img.shields.io/badge/Pytest-147%20Passed-brightgreen.svg?logo=pytest)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**SecureOps** is an enterprise-grade, provider-agnostic **AI Agent Security Gateway, Tool Execution Firewall & Adversarial Benchmark Engine**.

It enforces **Zero LLM Autonomy**: language models never act as final authorization authorities. Every prompt, execution request, and tool invocation is filtered through multi-provider classification, server-side deterministic policy enforcement, strict tenant isolation, deep argument inspection, and Human-In-The-Loop (HITL) approval gates before execution.

Additionally, SecureOps provides the **Adversarial Benchmark Engine (`security-baseline-v1`)** with a bounded adaptive testing loop to security-test real external AI agents (OpenAI, Groq, vLLM, LangChain, CrewAI, AutoGen, Custom REST) across 20 attack categories.

---

## 🌐 Live Production Deployments

| Component | Service Provider | Live Production URL |
| :--- | :--- | :--- |
| **Frontend Security Console** | **Vercel** | [https://secure-ops-pi.vercel.app](https://secure-ops-pi.vercel.app) |
| **API Security Gateway** | **Render** | [https://secureops-gateway.onrender.com](https://secureops-gateway.onrender.com) |
| **Interactive Swagger Docs** | **FastAPI / Render** | [https://secureops-gateway.onrender.com/docs](https://secureops-gateway.onrender.com/docs) |
| **Public Liveness Probe** | **Render Gateway** | [https://secureops-gateway.onrender.com/health](https://secureops-gateway.onrender.com/health) |
| **Subsystem Readiness Probe** | **Render Gateway** | [https://secureops-gateway.onrender.com/ready](https://secureops-gateway.onrender.com/ready) |

### Governed Dashboard Deep Links
- 📊 **Overview**: [https://secure-ops-pi.vercel.app/dashboard](https://secure-ops-pi.vercel.app/dashboard)
- 🛡️ **Request Gateway**: [https://secure-ops-pi.vercel.app/gateway](https://secure-ops-pi.vercel.app/gateway)
- ✋ **Approval Center**: [https://secure-ops-pi.vercel.app/approvals](https://secure-ops-pi.vercel.app/approvals)
- 🚨 **Security Events**: [https://secure-ops-pi.vercel.app/security-events](https://secure-ops-pi.vercel.app/security-events)
- 📜 **Audit Explorer**: [https://secure-ops-pi.vercel.app/audit](https://secure-ops-pi.vercel.app/audit)
- ⚡ **Execution Center**: [https://secure-ops-pi.vercel.app/executions](https://secure-ops-pi.vercel.app/executions)
- 🔧 **Tool Governance**: [https://secure-ops-pi.vercel.app/tools](https://secure-ops-pi.vercel.app/tools)
- 🏢 **Multi-Tenancy**: [https://secure-ops-pi.vercel.app/tenants](https://secure-ops-pi.vercel.app/tenants)
- 👥 **Users & Roles**: [https://secure-ops-pi.vercel.app/rbac](https://secure-ops-pi.vercel.app/rbac)
- 🔑 **API Credentials**: [https://secure-ops-pi.vercel.app/credentials](https://secure-ops-pi.vercel.app/credentials)
- 🩺 **System Health**: [https://secure-ops-pi.vercel.app/health](https://secure-ops-pi.vercel.app/health)
- ⚙️ **Settings**: [https://secure-ops-pi.vercel.app/settings](https://secure-ops-pi.vercel.app/settings)

---

## 🛡️ Key Capabilities

- 🛡️ **Deterministic Policy Engine**: Enforces canonical anti-downgrade matrices. Destructive actions (e.g. `delete_data`, `wipe_database`) unconditionally require human approval regardless of LLM output or client prompt manipulation.
- 🤖 **Universal Agent Compatibility**:
  - **`OpenAICompatibleAgentAdapter`**: Connects OpenAI, Groq, vLLM, LocalAI, Ollama, and Mistral agents with dynamic secret resolution and safe mocked fallback.
  - **`GenericHTTPAgentAdapter`**: Connects enterprise internal REST agents (LangChain, LangGraph, CrewAI, AutoGen) with SSRF protection, open redirect blocking (`follow_redirects=False`), 2MB payload caps, and production HTTPS enforcement.
  - **`SimulatedAgentAdapter`**: Offline sandbox simulator for safe deterministic test execution.
- 🎯 **Standard Adversarial Benchmark Engine (`security-baseline-v1`)**:
  - 20 baseline security attack scenarios across 6 domains (Prompt Injection, Jailbreaks, System Prompt Extraction, Tool Abuse, PII Exfiltration, SSRF, Path Traversal, Command Injection, Privilege Escalation).
  - **Adaptive Feedback Loop**: Triggers targeted multi-stage attack variants (`PI-002`, `MA-002`, `SSRF-002`, `PE-002`) within strict bounds (`MAX_ADAPTIVE_REQUESTS = 10`).
- 🔧 **Tool Security Gateway**:
  - Normalizes tool calls (`NormalizedToolCall`) across all agent architectures.
  - Enforces per-agent tool allowlists and deep regex inspection against shell command injection, path traversal (`../`), and SSRF destinations.
- 🏢 **Authoritative Server-Side Multi-Tenancy**:
  - All database queries, audit logs, approval tickets, rate limits, and credentials are partitioned by `tenant_id` via `TenantUserContext`. Cross-tenant access is blocked with `HTTP 403 Forbidden`.
- 🗄️ **PostgreSQL & Redis Dual-Engine Persistence**:
  - PostgreSQL persistence with async SQLAlchemy + `asyncpg` and Alembic migrations (`001_initial_tables` $\rightarrow$ `004_agent_benchmarks`).
  - Redis / Upstash sliding-window token-bucket rate limiter with automatic in-memory fallback.
- ✋ **Human-In-The-Loop (HITL) Approvals**: Time-bound, single-use approval tickets with HMAC-SHA256 webhooks (e.g. n8n integration).
- 📊 **Enterprise Glassmorphism Dashboard**: Real-time React + Vite + TypeScript frontend for threat monitoring, live agent scoring, audit logs, and SIEM security events.

---

## 🏛️ High-Level System Architecture

```text
                                SecureOps Gateway Architecture

 [ Client / Agent / Frontend ]
             │
             │  1. HTTP Request (Bearer API Key / Tenant Context)
             v
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      FastAPI Gateway Pipeline                          │
 │                                                                        │
 │  [ Bearer Auth & Tenant Resolution ] ──> TenantUserContext (Server-side)│
 │  [ Rate Limiter & Payload Guard ]   ──> Max 1MB / Max 4000 Chars       │
 │                                                                        │
 │  [ AI Classification Chain ]                                           │
 │     ├── Primary AI Provider (OpenAI / OpenRouter)                      │
 │     ├── Fallback 1: Google Gemini (gemini-3.5-flash)                   │
 │     └── Fallback 2: Groq (openai/gpt-oss-20b)                         │
 │                                                                        │
 │  [ Deterministic Policy Engine ]                                       │
 │     └── Overrides LLM risk -> Enforces Canonical Rules & Risk Gates    │
 └──────────────────────────────────┬─────────────────────────────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           │                                                 │
           v (If ALLOW)                                      v (If REQUIRE_APPROVAL)
 ┌───────────────────────────┐                     ┌───────────────────────────┐
 │   Tool Security Gateway   │                     │   HITL Approval Ticket    │
 │                           │                     │                           │
 │ ├── Tool Allowlist Check  │                     │ ├── HMAC Signed Webhook   │
 │ ├── SSRF / Private IP Blk │                     │ ├── Time-bound Expiry     │
 │ ├── Path Traversal Filter │                     │ └── Security Officer Gate │
 │ └── Shell Escape Filter   │                     └─────────────┬─────────────┘
 └─────────────┬─────────────┘                                   │
               │                                                 │
               └────────────────────────┬────────────────────────┘
                                        v
                            ┌───────────────────────┐
                            │ Audit & SIEM Logging  │
                            │                       │
                            │ ├── PostgreSQL / async│
                            │ ├── Security Events   │
                            │ └── Redacted JSON Log │
                            └───────────────────────┘
```

---

## 📁 Project Structure

```text
SecureOps/
├── secureops/                 # FastAPI Backend Engine & Benchmark Core
│   ├── alembic/               # Database Migration Versions (001 -> 004)
│   │   └── versions/          # 003_agent_security_gateway.py, 004_agent_benchmarks.py
│   ├── app/
│   │   ├── main.py            # Gateway Pipeline, Middleware & API Endpoints
│   │   ├── config.py          # Settings & Production Config Validation
│   │   ├── adapters/          # Universal Agent Adapters (OpenAI, HTTP, Simulated)
│   │   ├── routes/            # Agents, Evaluations, Benchmarks, Summary Endpoints
│   │   ├── schemas/           # Pydantic Schemas (Request, Decision, Agent, Approval)
│   │   ├── security/          # Policy Engine, Tool Gateway, Auth, RBAC, SSRF, Rate Limit
│   │   │   └── benchmarks/    # Benchmark Engine, Scorecard, Adaptive Testing
│   │   ├── ai/                # AI Providers (Gemini, Groq) & Fallback Classifier
│   │   ├── approval/          # HITL Approval Ticket Lifecycle Manager
│   │   ├── audit/             # Audit Logging, Metrics & SIEM Security Events
│   │   ├── db/                # PostgreSQL Models & Async Session Factory
│   │   ├── executor/          # Tool Dispatcher & Execution Sandbox
│   │   └── tools/             # Tool Registry & Document Service Adapter
│   ├── docs/                  # Architecture, Integration & Benchmark Documentation
│   ├── scripts/
│   │   ├── demo_universal_agent.py # End-to-end agent evaluation demo
│   │   └── secret_scan.py     # Hardcoded secret scanner
│   ├── test_documents/        # Isolated Tenant Document Repositories
│   └── tests/                 # 147+ Automated Pytest Security & Regression Tests
│
├── frontend/                  # React + Vite + TypeScript Dashboard (Vercel)
│   ├── src/
│   │   ├── components/        # Layout & Glassmorphism Dashboard Views
│   │   ├── context/           # Tab-Scoped AuthContext (sessionStorage)
│   │   ├── services/          # API Client & Header Sanitization
│   │   └── types/             # TypeScript API Interfaces
│   ├── vercel.json            # Vercel SPA Client-Side Routing Fallback
│   └── package.json
│
├── docker-compose.yml         # Containerized Infrastructure (PostgreSQL, Redis)
├── ARCHITECTURE.md            # Comprehensive Architectural Specification
├── SECURITY_SCORECARD.md      # Category Risk Breakdown & Defense Matrix
└── README.md                  # Project Overview & Setup Guide
```

---

## ⚡ Quickstart Guide

### Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: v18 or higher
- **PostgreSQL**: (e.g. Supabase, AWS RDS, or local Docker)
- **Redis**: (optional: Upstash REST or local Redis)

---

### Backend Setup (FastAPI Gateway)

1. **Navigate to backend directory**:
   ```bash
   cd secureops
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   *Example `.env` snippet*:
   ```env
   API_KEY=secops_live_your_secret_key
   ENVIRONMENT=development
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/secureops
   REDIS_URL=redis://localhost:6379/0
   GEMINI_API_KEY=your_gemini_key
   GROQ_API_KEY=your_groq_key
   CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,https://secure-ops-pi.vercel.app
   ```

5. **Apply database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Run security verification & test suite**:
   ```bash
   python -m pytest -v
   python scripts/secret_scan.py
   ```

7. **Start API server**:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```
   - **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

8. **Run Universal Agent Benchmark Demo**:
   ```bash
   python scripts/demo_universal_agent.py
   ```

---

### Frontend Setup (React / Vite)

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```
   - **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173) (or `http://localhost:3000`)

4. **Run unit tests & production build**:
   ```bash
   npm run test
   npm run build
   ```

---

## 📡 Key API Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/health` | Public server liveness check | No |
| `GET` | `/ready` | Gateway & subsystem readiness check | No |
| `POST` | `/v1/requests` | Primary AI Gateway classification & execution | Yes (Bearer) |
| `POST` | `/v1/executions` | Execution Center direct tool execution | Yes (Bearer) |
| `GET` | `/v1/approvals` | List pending/historical HITL approval tickets | Yes (Approver+) |
| `POST` | `/v1/approvals/{id}/approve` | Approve a pending ticket | Yes (Approver+) |
| `POST` | `/v1/approvals/{id}/reject` | Reject a pending ticket | Yes (Approver+) |
| `GET` | `/v1/audit/events` | Query tenant audit log history | Yes (Bearer) |
| `GET` | `/v1/security/events` | Query SIEM security threat events | Yes (Bearer) |
| `GET` | `/v1/dashboard/summary` | Query tenant dashboard metrics summary | Yes (Bearer) |
| `POST` | `/v1/credentials` | Generate new API credential | Yes (Admin+) |
| `GET` / `POST` | `/v1/agents` | List or register external AI agents | Yes (Bearer) |
| `GET` / `DELETE`| `/v1/agents/{id}` | Retrieve or decommission registered agent | Yes (Bearer) |
| `POST` | `/v1/agents/{id}/benchmarks` | Run adversarial benchmark against agent | Yes (Bearer) |
| `GET` | `/v1/benchmarks/{id}` | Retrieve benchmark findings & scorecard | Yes (Bearer) |

---

## 🎯 Adversarial Benchmark Suite (`security-baseline-v1`)

| Domain | Tests Evaluated | Enforcement Outcome |
| :--- | :--- | :--- |
| **Prompt Security** | Direct Injection (`PI-001`), DAN Jailbreak (`JB-001`), System Prompt Extraction (`SE-001`), Context Manipulation (`CM-001`), Indirect Injection (`IDI-001`) | `BLOCK` |
| **Tool Security** | Tool Abuse (`TA-001`), Unauthorized Invocation (`UT-001`), Malicious Arguments (`MA-001`), Excessive Execution (`ET-001`) | `REQUIRE_APPROVAL` / `BLOCK` |
| **Data Security** | Secret Extraction (`SL-001`), PII Exfiltration (`DE-001`), Cross-User Access (`CU-001`), Cross-Tenant Access (`CT-001`) | `BLOCK` |
| **Network Security** | Cloud Metadata SSRF (`SSRF-001`), Private IP / Loopback Blocking | `BLOCK` |
| **Filesystem / Exec** | Path Traversal (`PT-001`), Shell Command Injection (`CI-001`) | `BLOCK` |
| **Authorization** | Privilege Escalation (`PE-001`), Client Policy Override Injection (`AB-001`), Rate Limit Spoofing (`RL-001`) | `BLOCK` |

---

## ✅ Quality Assurance & Verification Metrics

- **Vitest Frontend Tests**: **39 / 39 PASS (100%)**
- **Pytest Backend Tests**: **147 / 147 PASS (100%)**
- **Hardcoded Secret Scanner**: **0 Secrets Detected**
- **Vercel SPA Client-Side Routing**: **Verified across all 12 deep links**
- **Live HTTP Real-World Socket Verification**: **Verified**
- **Open Vulnerabilities**: **0 Critical / 0 High**

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).