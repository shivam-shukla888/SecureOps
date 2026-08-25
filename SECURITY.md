# SecureOps Security Policy & Governance Guide

## Fundamental Security Posture

SecureOps enforces a zero-trust governance model for AI-driven tool execution:

> **The LLM suggests classification; the Python Deterministic Policy Engine enforces authorization; the Tool Permission Engine isolates execution; Multi-Tenancy partitions data.**

---

## Security Controls Summary

1. **Hashed API Credentials**: Raw API keys are never stored in database records. All keys are hashed with `SHA-256` and bound to a `tenant_id` and `user_id`.
2. **Server-Side RBAC**: Authorization is evaluated server-side. Users cannot assign themselves roles or override policy decisions.
3. **Multi-Tenant Data Isolation**: All persisted objects (`audit_logs`, `approval_tickets`, `execution_records`, `idempotency_records`) are partitioned by `tenant_id`.
4. **Cryptographic & Logical Ticket Binding**: Approval tickets are strictly bound to `request_id`, `user_id`, `intent`, `resource`, and expiration.
5. **SSRF & Outbound Network Policy**: Destinations are checked against `ALLOWED_OUTBOUND_HOSTS`. Access to `localhost`, loopbacks, private IPs, and cloud metadata endpoints (`169.254.169.254`) is forbidden.
6. **Secret Isolation**: Tools access secrets via `SecretProvider` with an explicit key allowlist. Direct `os.environ` access is blocked.
7. **SIEM Exporters**: Security events (`AUTH_FAILURE`, `PROMPT_INJECTION`, `SSRF_BLOCK`, etc.) are exported via `ConsoleSIEMExporter` and `WebhookSIEMExporter` adapters.

---

## Dependency & Repository Auditing

Run dependency vulnerability audit:
```bash
pip install pip-audit
pip-audit -r secureops/requirements.txt
```

Run repository secret scan:
```bash
python secureops/scripts/secret_scan.py
```
