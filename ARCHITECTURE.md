# System Architecture & Security Analysis: SecureOps (Phase 5 Enterprise Gateway)

## 1. Executive Summary

This document details the complete technical architecture and security design for **SecureOps (Phase 5)**. The system is a production-hardened Enterprise AI Request Gateway, Multi-Provider Fallback Classifier, Deterministic Security Policy Engine, Multi-Tenant Control Plane, and Secure Tool Executor built with Python and FastAPI.

The core principle governing SecureOps is:
> **The LLM suggests classification; the Python Deterministic Policy Engine enforces authorization; the Tool Permission Engine isolates execution; Multi-Tenancy partitions data.**

---

## 2. Phase 5 Multi-Tenant Pipeline Architecture

```text
                                  PHASE 5 MULTI-TENANT ARCHITECTURE

  +-------------------+
  | Client / API Key  |
  +---------+---------+
            |
            | 1. mTLS / Hashed Bearer Token (HSTS, Nosniff, Frame Options)
            v
  +---------------------------------------------------------------------------------+
  | Backend Gateway Service (FastAPI)                                               |
  |                                                                                 |
  |  +------------------+    +--------------------+    +-------------------------+  |
  |  | 2. Hashed Auth & | -> | 3. Input Guard &   | -> | 4. AI Provider Chain    |  |
  |  |    Tenant Context|    |    Sanitizer       |    |    (Gemini -> Groq)     |  |
  |  +------------------+    +--------------------+    +------------+------------+  |
  |                                                                 |               |
  |                                                                 v               |
  |                          +----------------------------------------------+       |
  |                          | 5. Deterministic Security Policy Engine      |       |
  |                          +----------------------+-----------------------+       |
  |                                                 |                               |
  +-------------------------------------------------|-------------------------------+
                                                    |
                       +----------------------------+----------------------------+
                       | (Decision == ALLOW)                                     | (Decision == REQUIRE_APPROVAL)
                       v                                                         v
  +------------------------------------------+    +------------------------------------------+
  | Tool Permission Engine                   |    | Approval Manager & n8n Webhook           |
  | - Server-Side Intent -> Tool Allowlist   |    | - Tenant-Scoped Approval Tickets         |
  | - Cryptographic & Logical Ticket Binding |    | - Self-Approval Prevention (403)         |
  | - Strict Pydantic Tool Input Validation  |    | - Replay Protection (300s Timestamp)     |
  +--------------------+---------------------+    +---------------------+--------------------+
                       |                                                |
                       +----------------------------+-------------------+ (Post Approval)
                                                    |
                                                    v
  +---------------------------------------------------------------------------------+
  | Secure Execution & Integration Layer                                            |
  | - DocumentServiceAdapter (Real Safe Read-Only Integration)                      |
  | - Multi-Tenant Data Partitioning (tenant_id Scoping)                            |
  | - Secret Isolation (SecretProvider Allowlist)                                   |
  | - Outbound SSRF Protection (ALLOWED_OUTBOUND_HOSTS)                             |
  | - Idempotency-Key Caching (tenant_id:user_id:key)                               |
  | - Execution Timeout Control (asyncio.wait_for)                                  |
  | - SIEM Security Event Exporters (Console & Webhook)                             |
  | - Persistent Redacted Audit Logging (PostgreSQL)                                |
  +---------------------------------------------------------------------------------+
```

---

## 3. Production Deployment Architecture Options

### Option A: Cloudflare + SecureOps Container Infrastructure

```text
External Client
       ↓
Cloudflare Edge WAF (TLS 1.3, DDoS Mitigation, Rate Limiting, Geo-Blocking, Bot Control)
       ↓
Ingress Load Balancer (mTLS Client Certificate Termination)
       ↓
SecureOps API Gateway (FastAPI Containers in K8s / ECS)
       ↓                             ↓
PostgreSQL DB (RDS/Managed)     Redis Cluster (ElastiCache)
```

### Option B: AWS Enterprise Infrastructure

```text
External Client
       ↓
AWS WAF (OWASP Top 10 Rules, IP Reputation, Rate Control)
       ↓
AWS Application Load Balancer (ALB with TLS 1.3 & mTLS Auth)
       ↓
SecureOps ECS Fargate / EKS Cluster
       ↓                             ↓
AWS Aurora PostgreSQL          AWS ElastiCache Redis
```

---

## 4. Comprehensive STRIDE Threat Model & Mitigations

| STRIDE Category | Vector | Phase 5 Mitigation Control |
| :--- | :--- | :--- |
| **Spoofing Identity** | Impersonating client, tenant, or approver | SHA-256 hashed Bearer API key lookup; `TenantUserContext` binding; self-approval prevention (`requester != approver`). |
| **Tampering** | Modifying parameters, cross-tenant mutation, or replay attacks | Multi-tenancy `tenant_id` scoping; strict Pydantic schemas (`extra="forbid"`); HMAC timestamp validation (300s window); tenant-scoped idempotency caching. |
| **Repudiation** | Denying tool execution or administrative changes | Redacted audit logging & SIEM security event exporters capturing `event_id`, `tenant_id`, `user_id`, `request_id`, `severity`, and `latency_ms`. |
| **Information Disclosure** | Cross-tenant data leaks or secret exfiltration | Multi-tenant database queries (`WHERE tenant_id = :tenant_id`); SecretProvider key allowlist isolation; unified JSON error outputs. |
| **Denial of Service** | Resource exhaustion, oversized payloads, or SSRF loops | Redis sliding-window rate limiting; `MAX_REQUEST_SIZE_BYTES` caps; `EXECUTION_TIMEOUT_SECONDS` cancellation wrappers (`asyncio.wait_for`). |
| **Elevation of Privilege** | Self-assigning roles or prompt injection jailbreaks | Server-side RBAC enforcement (`require_role`); Deterministic Security Policy Engine overriding LLM classifications. |

---

## 5. Automated Regression Test Suite Verification

The regression test suite (`python -m pytest -v`) validates 88 test cases across 18 test modules with **100% pass rate**:

- **Auth, Credentials & Multi-Tenancy (12 tests)**: Hashed API key authentication, key creation, rotation, revocation, cross-tenant isolation, and RBAC role restrictions.
- **Adversarial Security Tests (19 tests)**: Prompt injections, sysadmin claims, parameter overrides, command injection, SSRF, path traversal, SQL injection, replayed/expired approvals, and provider outages.
- **Deterministic Policy & AI Fallback (12 tests)**: Policy risk baselines, anti-downgrade overrides, Gemini $\rightarrow$ Groq fallback chain, fail-closed posture.
- **HITL Approvals & Self-Approval Prevention (6 tests)**: Lifecycle status transitions, ticket expiration, double approval, and self-approval 403 checks.
- **HMAC Webhooks & Replay Protection (4 tests)**: HMAC signature calculation, invalid signature, timestamp replay window.
- **Tool Permissions & Approval Binding (7 tests)**: Intent matching, missing approval, resource mismatch, request ID mismatch.
- **SSRF & Secret Isolation (5 tests)**: Localhost, cloud metadata, private IP, unallowlisted host, and unauthorized secret key rejection.
- **Idempotency & Execution Timeouts (2 tests)**: Duplicate `Idempotency-Key` caching and execution timeout 504 handling.
- **Persistence, SIEM & Config (11 tests)**: InMemoryAuditRepository, Redis rate limiter, SIEM event logging, safe DB adapter, and production startup config checks.
