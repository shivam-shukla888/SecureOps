# SecureOps — Enterprise AI Security Gateway & Zero-Trust Tool Firewall

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-emerald.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-cyan.svg)](https://react.dev/)
[![Security Audit](https://img.shields.io/badge/Security--Audit-100%25%20PASS-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**SecureOps** is an enterprise-grade AI Security Gateway designed to control and govern Large Language Model (LLM) agent interactions with internal databases, tools, and document repositories.

It guarantees **Zero LLM Autonomy**: the AI provider never acts as the final authorization authority. Every request undergoes multi-provider classification, server-side deterministic policy enforcement, strict tenant isolation, and optional Human-In-The-Loop (HITL) approval routing before any execution occurs.

---

## Key Capabilities

- 🛡️ **Deterministic Policy Engine**: Overrides LLM prompt injections or hallucinations. Destructive operations (e.g., `DELETE_DATA`, `UPDATE_DATA`) unconditionally require human approval regardless of what the LLM outputs.
- 🔄 **3-Tier AI Provider Fallback Chain**: Primary AI Provider -> Google Gemini (`gemini-3.5-flash`) -> Groq (`openai/gpt-oss-20b`). Automatically fails closed (`UNKNOWN` / `HIGH` risk -> `BLOCK`) if all providers are unavailable.
- 🏢 **Authoritative Server-Side Multi-Tenancy**: Tenant identity (`tenant_id`) is anchored strictly in authenticated credentials (`TenantUserContext`) and server-side token state. Natural language prompts or client parameters can never override tenant scope.
- 📄 **Real Read-Only Document Service**: Scoped document search querying tenant filesystem repositories (`test_documents/<tenant_id>/`) with path traversal protection and stop-word keyword filtering.
- ✋ **Human-In-The-Loop (HITL) Approval Engine**: Time-bound, single-use approval tickets with HMAC-signed outbound webhook notifications (e.g., n8n integration).
- 🌐 **SSRF & Secret Isolation**: Egress host allowlisting, private IP range blocking, cloud metadata URL protection (`169.254.169.254`), and isolated credential management.
- 📊 **Enterprise React Dashboard**: High-density glassmorphism frontend built with Vite, TypeScript, and Tailwind CSS for real-time threat monitoring, audit logs, and SIEM security events.

---

## High-Level System Architecture

```text
                               SecureOps Gateway Architecture

 [ User / Frontend Client ]
            │
            │  1. HTTP POST /v1/requests (Bearer API Key)
            v
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      FastAPI Gateway Pipeline                          │
 │                                                                        │
 │  [ Bearer Auth & Tenant Resolution ] ──> TenantUserContext (Server-side)│
 │  [ Rate Limiter & Payload Validator ] ──> Max 1MB / Max 4000 Chars     │
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
 │   Tool Execution Engine   │                     │   HITL Approval Ticket    │
 │                           │                     │                           │
 │ ├── DocumentServiceAdapter│                     │ ├── HMAC Signed n8n Webhook│
 │ ├── Read-Only Scoped Index│                     │ ├── Time-bound Expiration │
 │ └── Path Traversal Check  │                     │ └── Security Officer Review│
 └─────────────┬─────────────┘                     └─────────────┬─────────────┘
               │                                                 │
               └────────────────────────┬────────────────────────┘
                                        v
                            ┌───────────────────────┐
                            │ Audit & SIEM Logging  │
                            │                       │
                            │ ├── Memory/PG Storage │
                            │ └── Security Events   │
                            └───────────────────────┘
```

---

## Project Structure

```text
SecureOps/
├── secureops/                 # FastAPI Backend Engine
│   ├── app/
│   │   ├── main.py            # Gateway Routing & API Endpoints
│   │   ├── config.py          # Pydantic BaseSettings & Environment Config
│   │   ├── ai/                # AI Providers (Gemini, Groq, Primary) & Classifier
│   │   ├── approval/          # HITL Approval Ticket Lifecycle Manager
│   │   ├── audit/             # Audit Logging & SIEM Event Recording
│   │   ├── executor/          # Dispatcher & Server-Side Execution Engine
│   │   ├── security/          # Auth, RBAC, Policy Engine, Rate Limiter, SSRF
│   │   └── tools/             # Tool Registry, Schemas & DocumentServiceAdapter
│   ├── test_documents/        # Isolated Tenant Document Repository
│   │   ├── tenant_default/    # Architecture & Governance Docs
│   │   ├── tenant_acme/       # Acme Confidential Docs
│   │   └── tenant_globex/     # Globex Financial Docs
│   ├── tests/                 # 102 Backend Pytest Security & Integration Tests
│   └── scripts/               # Secret Scanner (`secret_scan.py`)
│
├── frontend/                  # React + Vite + TypeScript Frontend
│   ├── src/
│   │   ├── components/        # Layout & Glassmorphism Dashboard Views
│   │   ├── context/           # Tab-Scoped AuthContext (sessionStorage)
│   │   ├── services/          # API Client & Header Sanitization
│   │   └── types/             # TypeScript API Interfaces
│   └── package.json
│
├── SECURITY_QA_REPORT.md      # Adversarial Audit Report (50 Security Categories)
└── SECURITY_TEST_MATRIX.md    # Detailed Defense & Test Evaluation Matrix
```

---

## Quickstart Guide

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: v18 or higher
- **Git**

---

### Backend Setup (FastAPI)

1. **Navigate to the backend directory**:
   ```bash
   cd secureops
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Copy `.env.example` to `.env` and add your provider API keys:
   ```bash
   cp .env.example .env
   ```
   *Example `.env` snippet*:
   ```env
   API_KEY=secops_live_your_secret_key
   ENVIRONMENT=development
   GEMINI_API_KEY=your_gemini_key
   GEMINI_MODEL=gemini-3.5-flash
   GROQ_API_KEY=your_groq_key
   GROQ_MODEL=openai/gpt-oss-20b
   ```

5. **Run the test suite**:
   ```bash
   python -m pytest -v
   python scripts/secret_scan.py
   ```

6. **Start the API server**:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```
   - **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

### Frontend Setup (React / Vite)

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run unit tests**:
   ```bash
   npx vitest run
   ```

4. **Start the development server**:
   ```bash
   npm run dev
   ```
   - **Frontend App**: [http://localhost:3000](http://localhost:3000)

5. **Build for production**:
   ```bash
   npm run build
   ```

---

## Key API Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/health` | Server health check | No |
| `GET` | `/ready` | Gateway & subsystem readiness check | No |
| `POST` | `/v1/requests` | Primary AI Gateway classification & execution | Yes (Bearer) |
| `POST` | `/v1/executions` | Execution Center direct tool execution | Yes (Bearer) |
| `GET` | `/v1/approvals` | List pending/historical HITL approval tickets | Yes (Approver+) |
| `POST` | `/v1/approvals/{id}/approve` | Approve a pending ticket | Yes (Approver+) |
| `POST` | `/v1/approvals/{id}/reject` | Reject a pending ticket | Yes (Approver+) |
| `GET` | `/v1/audit/events` | Query tenant audit log history | Yes (Bearer) |
| `GET` | `/v1/security/events` | Query SIEM security threat events | Yes (Bearer) |
| `GET` | `/v1/dashboard/summary` | Query tenant dashboard metrics summary | Yes (Bearer) |
| `POST` | `/v1/credentials` | Generate new API credential (Admin/Owner) | Yes (Admin+) |

---

## Security Verification & Quality Assurance

SecureOps has undergone thorough adversarial QA testing across 50 security dimensions, detailed in [`SECURITY_QA_REPORT.md`](file:///c:/Users/thesh/OneDrive/Desktop/SecureOps/SECURITY_QA_REPORT.md) and [`SECURITY_TEST_MATRIX.md`](file:///c:/Users/thesh/OneDrive/Desktop/SecureOps/SECURITY_TEST_MATRIX.md).

- **Pytest Suite**: **102 / 102 PASS**
- **Frontend Test Suite**: **3 / 3 PASS**
- **Hardcoded Secret Scanner**: **0 Secrets Detected**
- **Open Vulnerabilities**: **0 Critical / 0 High**

---

## License

This project is licensed under the [MIT License](LICENSE).