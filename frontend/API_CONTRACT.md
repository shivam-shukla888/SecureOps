# SecureOps Frontend API Contract Specification

This document defines the exact API integration contract between the **SecureOps Frontend Platform** (`frontend/`) and the **FastAPI Security Gateway** (`http://127.0.0.1:8000`).

---

## Authorization & Headers

All authenticated requests include:
```http
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

---

## Endpoint Contract Specifications

### 1. Health Liveness Check
- **Endpoint**: `GET /health`
- **Auth Required**: No
- **Response**:
  ```json
  {
    "status": "healthy",
    "service": "SecureOps API Gateway",
    "timestamp": "2026-08-25T17:00:00Z"
  }
  ```

### 2. System Readiness Check
- **Endpoint**: `GET /ready`
- **Auth Required**: No
- **Response**:
  ```json
  {
    "status": "ready",
    "rate_limiter": "ready",
    "database": "ready",
    "timestamp": "2026-08-25T17:00:00Z"
  }
  ```

### 3. Request Security Gateway
- **Endpoint**: `POST /v1/requests`
- **Auth Required**: Yes (Bearer Token)
- **Request Body**:
  ```json
  {
    "user_id": "operator_alice",
    "request": "Search my documents for the architecture document."
  }
  ```
- **Response (ALLOW)**:
  ```json
  {
    "request_id": "req_12345",
    "user_id": "operator_alice",
    "intent": "SEARCH_DOCUMENT",
    "resource": "docs",
    "ai_risk": "LOW",
    "policy_risk": "LOW",
    "requires_approval": false,
    "decision": "ALLOW",
    "override_applied": false,
    "provider_used": "gemini",
    "fallback_used": false,
    "execution_result": { "status": "executed", "data": [...] },
    "timestamp": "2026-08-25T17:00:00Z"
  }
  ```

### 4. Human-In-The-Loop Approvals List
- **Endpoint**: `GET /v1/approvals`
- **Query Params**: `status` (optional: PENDING, APPROVED, REJECTED, EXPIRED)
- **Auth Required**: Yes (Role: `APPROVER`, `ADMIN`, `OWNER`)
- **Response**:
  ```json
  {
    "tenant_id": "tenant_default",
    "count": 1,
    "approvals": [
      {
        "approval_id": "appr_100",
        "request_id": "req_100",
        "requester_id": "user_alice",
        "intent": "UPDATE_DATA",
        "resource": "database",
        "policy_risk": "MEDIUM",
        "status": "PENDING",
        "created_at": "2026-08-25T17:00:00Z",
        "expires_at": "2026-08-25T18:00:00Z"
      }
    ]
  }
  ```

### 5. Approve Request Ticket
- **Endpoint**: `POST /v1/approvals/{approval_id}/approve`
- **Auth Required**: Yes (Role: `APPROVER`, `ADMIN`, `OWNER`)
- **Request Body**:
  ```json
  {
    "approver_id": "security_officer_bob"
  }
  ```

### 6. Reject Request Ticket
- **Endpoint**: `POST /v1/approvals/{approval_id}/reject`
- **Auth Required**: Yes (Role: `APPROVER`, `ADMIN`, `OWNER`)
- **Request Body**:
  ```json
  {
    "approver_id": "security_officer_bob"
  }
  ```

### 7. Audit Events Stream
- **Endpoint**: `GET /v1/audit/events`
- **Query Params**: `limit=50`, `user_id`, `decision`
- **Auth Required**: Yes (Role: `VIEWER`, `OPERATOR`, `APPROVER`, `ADMIN`, `OWNER`)

### 8. SIEM Security Events Telemetry
- **Endpoint**: `GET /v1/security/events`
- **Query Params**: `limit=50`
- **Auth Required**: Yes

### 9. Dashboard Command Center Summary
- **Endpoint**: `GET /v1/dashboard/summary`
- **Auth Required**: Yes

### 10. Tool Execution Dispatcher
- **Endpoint**: `POST /v1/executions`
- **Auth Required**: Yes

### 11. Create API Credential
- **Endpoint**: `POST /v1/credentials`
- **Auth Required**: Yes (Role: `ADMIN`, `OWNER`)

---

## Status Code Handling Matrix

| HTTP Code | Exception Category | Frontend Behavior |
| :--- | :--- | :--- |
| `401` | Unauthorized | Redirect to Login Screen |
| `403` | Forbidden (RBAC / Self-Approval) | Display "Access Denied" Banner |
| `429` | Rate Limit Exceeded | Toast notification: "Too many requests. Please wait." |
| `503` | Service Unavailable | Show Gateway Disconnected Warning |
