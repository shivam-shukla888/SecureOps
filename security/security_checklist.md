# SecureOps Production Deployment Security Checklist

This operational checklist must be verified prior to deploying SecureOps to production infrastructure.

---

## 1. Authentication & Network Edge

- [x] **Bearer Token Security**: `API_KEY` set to a cryptographically strong random string (>= 32 chars).
- [ ] **mTLS Ingress Termination**: Mutual TLS (mTLS) client certificate verification configured at Load Balancer / API Gateway.
- [ ] **WAF Edge Deployment**: Cloudflare WAF or AWS WAF enabled with OWASP Top 10 rules, rate limiting, and geo-blocking.

---

## 2. Infrastructure & Persistence

- [x] **Non-Root Docker Execution**: Docker container runs under dedicated `appuser` non-root account.
- [x] **Database Isolation**: PostgreSQL configured with SSL/TLS connection strings and parameterized ORM queries.
- [x] **Redis Rate Limiting**: Redis instance configured with authentication password and TLS connection.

---

## 3. Application Security Controls

- [x] **Deterministic Security Policy**: Canonical risk baselines enforced in Python above LLM outputs.
- [x] **Self-Approval Prevention**: Requester cannot approve their own high-risk approval ticket (`approver_id != requester_id`).
- [x] **SSRF Protection**: Outbound network policy restricts destinations to `ALLOWED_OUTBOUND_HOSTS`.
- [x] **Secret Provider Isolation**: Direct `os.environ` access blocked; secret access restricted to allowlist.
- [x] **Path Traversal & Injection Sanitization**: Input fields validated against path traversal (`../`) and command injection regexes.
- [x] **HMAC Replay Protection**: Outbound webhooks signed with HMAC-SHA256 and checked for 300s timestamp expiration.
- [x] **Redacted Audit Logging**: Loggers configured to redact API keys, tokens, passwords, and raw secrets.
