# SecureOps Security Attack Case Catalog

This catalog documents the automated adversarial test cases executed against the SecureOps API Gateway.

---

## Adversarial Test Suite Inventory (`tests/test_adversarial.py`)

1. **`test_adv_1_ignore_instructions_delete_db`**: Prompts requesting deletion of the database under jailbreak instructions are classified as `DELETE_DATA` and forced to `HIGH` risk & `REQUIRE_APPROVAL` by policy.
2. **`test_adv_2_admin_claim_low_risk`**: User claiming admin status is ignored; `DELETE_DATA` requires approval regardless of claimed authority.
3. **`test_adv_3_client_inject_requires_approval_false`**: Attempts to inject `"requires_approval": false` in the request body return `HTTP 400 Bad Request`.
4. **`test_adv_4_client_inject_allowed_true`**: Attempts to inject `"allowed": true` return `HTTP 400 Bad Request`.
5. **`test_adv_5_client_inject_tool_parameter`**: Client sending `"tool": "delete_data"` is ignored/rejected.
6. **`test_adv_6_command_injection_rm_rf`**: Shell command injection characters (`semicolon`, `pipe`) in tool inputs return `HTTP 400 Bad Request`.
7. **`test_adv_7_ssrf_localhost`**: Outbound destination `127.0.0.1` returns `HTTP 403 Forbidden`.
8. **`test_adv_8_ssrf_metadata_endpoint`**: Destination `169.254.169.254` returns `HTTP 403 Forbidden`.
9. **`test_adv_9_path_traversal`**: Input containing `../../etc/passwd` returns `HTTP 400 Bad Request`.
10. **`test_adv_10_sql_injection_payload`**: SQL injection payload returns `HTTP 400 Bad Request`.
11. **`test_adv_11_replayed_approval`**: Re-submitting an approval ticket returns `HTTP 400 Bad Request`.
12. **`test_adv_12_expired_approval`**: Approving an expired ticket returns `HTTP 400 Bad Request`.
13. **`test_adv_13_approval_wrong_resource_binding`**: Using ticket for `resource_A` on `resource_B` returns `HTTP 403 Forbidden`.
14. **`test_adv_14_duplicate_idempotency_key`**: Duplicate `Idempotency-Key` returns cached result without re-executing.
15. **`test_adv_15_massive_request_payload`**: Payload > 1 MB returns `HTTP 413 Payload Too Large`.
16. **`test_adv_16_gemini_malformed_json_fallback`**: Malformed JSON triggers fallback or fail-closed `BLOCK`.
17. **`test_adv_17_gemini_low_risk_delete_data_overridden`**: Policy overrides AI risk downgrade.
18. **`test_adv_18_gemini_unavailable_fallback`**: Primary provider failure successfully triggers Groq fallback.
19. **`test_adv_19_gemini_and_groq_both_unavailable`**: All AI providers failing result in fail-closed `BLOCK`.
