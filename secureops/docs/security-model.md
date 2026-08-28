# SecureOps Security Model & Threat Boundary

## 1. Security Philosophy & Principles

1. **Zero LLM Authority**: Language models produce probabilistic predictions. They must NEVER be treated as authorization authorities or allowed to grant approval for protected operations.
2. **Deterministic Policy Supremacy**: All security-critical decisions are evaluated by server-side deterministic policy code enforcing strict least privilege, RBAC, and tenant boundaries.
3. **Fail-Closed by Design**: Any unexpected exception, timeout, unparseable argument, or ambiguous parameter automatically defaults to `BLOCK`.
4. **Zero Hardcoded Secrets**: Secrets and credentials are never stored in database records, never logged, and never included in benchmark findings or API payloads.

---

## 2. Threat Vector Defenses

### A. Prompt Injection & Jailbreaks
- **Defense**: Requests pass through the `IntentClassifier` detecting adversarial tokens and instruction overrides (`Ignore all prior instructions`, `DAN`, roleplay escapes).
- **Outcome**: Flagged as high-risk, evaluated as `BLOCK`, logged with correlation ID.

### B. Tool Abuse & Unauthorized Tool Execution
- **Defense**: `ToolSecurityGateway` matches requested tool name against the agent's explicit `allowed_tools` allowlist.
- **Outcome**: Unlisted tools are immediately `BLOCK`ed before execution. Dangerous actions (`delete_data`, `transfer_funds`) trigger `REQUIRE_APPROVAL` (HITL).

### C. Server-Side Request Forgery (SSRF)
- **Defense**: `SSRFProtector` resolves target hostnames and blocks:
  - Loopback IPs: `127.0.0.0/8`, `::1`, `localhost`
  - Cloud Metadata IPs: `169.254.169.254` (AWS/GCP/Azure)
  - RFC 1918 Private Subnets: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
  - Non-HTTP/HTTPS schemes (e.g. `file://`, `gopher://`, `ftp://`)

### D. Filesystem & Shell Injection
- **Defense**: Arguments are validated for directory traversal (`../`, `..\\`) and shell control characters (`;`, `|`, `&`, `\n`, `` ` ``).

### E. Multitenant Data Isolation
- **Defense**: Every API call requires authentication verifying tenant context (`ctx.tenant_id`). All PostgreSQL queries apply tenant-scoped WHERE clauses. Cross-tenant access is rejected with HTTP 403 / 404.

---

## 3. Policy Decision Matrix

| Request Characteristic | Security Check | Decision |
| :--- | :--- | :--- |
| Prompt injection detected | Classifier Confidence > 0.8 | `BLOCK` |
| Tool not in `allowed_tools` | Allowlist match | `BLOCK` |
| Malicious argument (SSRF/Cmd/Path) | ToolSecurityGateway regex | `BLOCK` |
| Destructive tool (`delete_data`) | High-impact action rule | `REQUIRE_APPROVAL` |
| Normal authorized tool | Allowlist + clean arguments | `ALLOW` |
