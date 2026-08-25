# SecureOps Architecture Specification

SecureOps is an enterprise-grade AI Security Gateway designed to enforce zero LLM tool autonomy.

## Core Architectural Pillars

1. **FastAPI Gateway**: Rate-limited, Bearer authenticated multi-tenant entrypoint.
2. **AI Provider Fallback Chain**: Google Gemini (Primary: `gemini-3.5-flash`) -> Groq (Fallback: `openai/gpt-oss-20b`).
3. **Deterministic Policy Engine**: Overrides LLM prompt injections and enforces canonical risk rules.
4. **Human-In-The-Loop (HITL) Approvals**: Time-bound approval tickets for destructive or medium/high-risk operations.
5. **Multi-Tenancy & Tenant Isolation**: Strict `tenant_id` scoping across audit logs, approval tickets, and document storage.
6. **Server-Side Tool Registry & Document Service**: Read-only, tenant-isolated document index querying local document repositories.
