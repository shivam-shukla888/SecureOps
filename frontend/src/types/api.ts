export type RoleEnum = 'OWNER' | 'ADMIN' | 'APPROVER' | 'OPERATOR' | 'VIEWER';
export type DecisionEnum = 'ALLOW' | 'REQUIRE_APPROVAL' | 'BLOCK';
export type RiskEnum = 'LOW' | 'MEDIUM' | 'HIGH';
export type IntentEnum = 'SEARCH_DOCUMENT' | 'READ_DATA' | 'SEND_DOCUMENT' | 'UPDATE_DATA' | 'DELETE_DATA' | 'UNKNOWN';

export interface HealthResponse {
  status: string;
  service: string;
  timestamp: string;
}

export interface ReadinessResponse {
  status: string;
  rate_limiter: string;
  database: string;
  metrics_summary: Record<string, any>;
  timestamp: string;
}

export interface SecurityGatewayResponse {
  request_id: string;
  user_id: string;
  intent: IntentEnum;
  resource: string;
  ai_risk: RiskEnum;
  policy_risk: RiskEnum;
  requires_approval: boolean;
  decision: DecisionEnum;
  override_applied: boolean;
  provider_used: string;
  fallback_used: boolean;
  approval_id?: string | null;
  expires_at?: string | null;
  execution_result: Record<string, any>;
  timestamp: string;
}

export interface ApprovalTicket {
  approval_id: string;
  request_id: string;
  requester_id: string;
  intent: string;
  resource: string;
  policy_risk: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED';
  approver_id?: string | null;
  created_at: string;
  expires_at: string;
}

export interface ApprovalsListResponse {
  tenant_id: string;
  count: number;
  approvals: ApprovalTicket[];
}

export interface ApprovalActionResult {
  request_id: string;
  approval_id: string;
  decision: string;
  status: string;
  message: string;
  approver_id: string;
  timestamp: string;
  execution_result: Record<string, any>;
}

export interface AuditEvent {
  request_id: string;
  tenant_id: string;
  user_id: string;
  intent: string;
  resource: string;
  ai_risk: string;
  policy_risk: string;
  final_decision: string;
  provider: string;
  fallback_used: boolean;
  latency_ms: number;
  error_status?: string | null;
  timestamp: string;
}

export interface AuditEventsResponse {
  tenant_id: string;
  count: number;
  events: AuditEvent[];
}

export interface SecurityEvent {
  event_id: string;
  event_type: string;
  severity: 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  tenant_id: string;
  user_id?: string | null;
  request_id?: string | null;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface SecurityEventsResponse {
  tenant_id: string;
  count: number;
  events: SecurityEvent[];
}

export interface DashboardSummaryResponse {
  tenant_id: string;
  user_id: string;
  role: RoleEnum;
  requests_today: number;
  allowed_requests: number;
  blocked_requests: number;
  pending_approvals: number;
  security_events: number;
  provider_fallbacks: number;
  metrics?: Record<string, any>;
  timestamp: string;
}

export interface ExecutionResponse {
  execution_id: string;
  request_id: string;
  status: string;
  tool_name: string;
  result: Record<string, any>;
  latency_ms: number;
  timestamp: string;
}

export interface APICredentialRecord {
  credential_id: string;
  tenant_id: string;
  user_id: string;
  name: string;
  role: RoleEnum;
  created_at: string;
}

export interface CreateCredentialResponse {
  status: string;
  api_key: string;
  credential: APICredentialRecord;
  warning: string;
}
