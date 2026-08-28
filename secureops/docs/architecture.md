# SecureOps System Architecture

## 1. Executive Summary

SecureOps is a production-grade, provider-agnostic **AI Agent Security Gateway and Adversarial Benchmark Testing Platform**. It enables organizations to connect arbitrary AI agents (OpenAI-compatible, Generic REST/HTTP, LangChain, CrewAI, AutoGen, Custom Python/Java, and Simulated Agents), subject them to automated adversarial testing suites, intercept and authorize their tool calls at runtime, and enforce deterministic security policies with zero LLM authority.

---

## 2. Gateway Pipeline & Data Flow

```
[ External / Internal AI Agent ]
               ↓
     [ BaseAgentAdapter ]
(OpenAI / Generic HTTP / Simulated)
               ↓
  [ NormalizedToolCall Stream ]
               ↓
   [ ToolSecurityGateway ]
(SSRF / Path / Command / Allowlist)
               ↓
     [ PolicyEngine (DSL) ]
(ALLOW / REQUIRE_APPROVAL / BLOCK)
               ↓
    [ RiskScoringEngine ]
 (Prompt + Tool + Data Risk)
               ↓
[ Benchmark & Finding Engine ]
 (security-baseline-v1 + Adaptive)
               ↓
[ SecureOps Security Scorecard ]
 (Domain breakdown & Overall Score)
               ↓
  [ Structured Audit & SIEM ]
```

---

## 3. Core Architecture Components

### A. Provider-Agnostic Adapter Layer (`app/adapters/`)
- **`BaseAgentAdapter`**: Standard interface providing normalized request/response execution, tool-call extraction, and health checks.
- **`OpenAICompatibleAgentAdapter`**: Connects any OpenAI-compatible provider (OpenAI, Groq, vLLM, LocalAI, Ollama). Extracts `tool_calls` into `NormalizedToolCall` objects.
- **`GenericHTTPAgentAdapter`**: Hardened for enterprise internal agents. Enforces open-redirect blocking (`follow_redirects=False`), 2MB response size limits, and HTTPS in production.
- **`SimulatedAgentAdapter`**: Safe execution simulator for sandbox evaluation without side-effects.

### B. Runtime Tool Security Gateway (`app/security/tool_gateway.py`)
- Intercepts all tool execution requests.
- Validates tool names against the agent's explicit `allowed_tools` allowlist.
- Inspects arguments for SSRF (cloud metadata, loopback, RFC 1918 private subnets), path traversal (`../`), and shell metacharacters (`;`, `|`, `&`, `\n`).

### C. Deterministic Policy Engine (`app/security/policy.py`)
- Rules are evaluated strictly on server-side state, user role, tenant ID, and tool risk.
- LLMs are **never** permitted to grant approval or override policy decisions.
- Outputs: `ALLOW`, `REQUIRE_APPROVAL` (triggers Human-In-The-Loop), or `BLOCK`.

### D. Benchmark & Scorecard Engine (`app/security/benchmarks/`)
- **`security-baseline-v1`**: 20 comprehensive security test cases covering Prompt Security, Tool Security, Data Security, Network Security, Filesystem/Execution, and Authorization/Reliability.
- **Adaptive Security Testing**: Safe loop triggering targeted scenario variants (`PI-002`, `MA-002`, `SSRF-002`, `PE-002`) within strict bounds (`max_iterations=3`, `max_requests=10`).
- **SecureOps Security Score**: Deterministic aggregate risk rating (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

### E. Persistence & Multitenancy Layer (`app/db/`, `app/security/rbac.py`)
- Multi-tenant data isolation on PostgreSQL with async SQLAlchemy + asyncpg.
- Alembic schema migrations: `001_initial_tables` -> `002_production_tables` -> `003_agent_security_gateway` -> `004_agent_benchmarks`.
- Distributed rate limiting and state management via Redis / Upstash REST.
