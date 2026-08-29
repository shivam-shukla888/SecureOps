import {
  HealthResponse,
  ReadinessResponse,
  SecurityGatewayResponse,
  ApprovalsListResponse,
  ApprovalActionResult,
  AuditEventsResponse,
  SecurityEventsResponse,
  DashboardSummaryResponse,
  ExecutionResponse,
  CreateCredentialResponse,
} from '../types/api';

export const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  const isBrowser = typeof window !== 'undefined';
  const isNonLocalhost = isBrowser && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';

  if (envUrl && typeof envUrl === 'string' && envUrl.trim().length > 0) {
    let cleanUrl = envUrl.trim().replace(/['"]/g, '').replace(/\/+$/, '');
    // Strip accidental trailing /v1 or /api so root endpoints (/health, /ready) and versioned endpoints (/v1/...) resolve accurately
    cleanUrl = cleanUrl.replace(/\/+(?:v1|api)\/?$/i, '').replace(/\/+$/, '');
    if ((import.meta.env.PROD || isNonLocalhost) && (cleanUrl.includes('localhost') || cleanUrl.includes('127.0.0.1'))) {
      return 'https://secureops-gateway.onrender.com';
    }
    return cleanUrl || 'https://secureops-gateway.onrender.com';
  }
  return 'https://secureops-gateway.onrender.com';
};

export const BASE_URL = getApiBaseUrl();

export class APIError extends Error {
  statusCode: number;
  data: any;

  constructor(message: string, statusCode: number, data?: any) {
    super(message);
    this.name = 'APIError';
    this.statusCode = statusCode;
    this.data = data;
  }
}

async function request<T>(path: string, options: RequestInit = {}, apiKey?: string): Promise<T> {
  const isPublicRootEndpoint = path === '/health' || path === '/ready' || path === 'health' || path === 'ready';

  const headers: Record<string, string> = {
    'Accept': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  // Only attach Content-Type if there is a request body (e.g. POST/PUT/PATCH)
  if (options.body && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  // Only attach Authorization header if not a public probe (/health or /ready)
  if (!isPublicRootEndpoint) {
    const rawToken = apiKey || sessionStorage.getItem('secureops_session_key') || '';
    if (rawToken) {
      // Strip any accidental duplicate Bearer/bearer prefixes or surrounding quotes
      let cleanToken = rawToken.trim().replace(/['"]/g, '');
      while (cleanToken.toLowerCase().startsWith('bearer ')) {
        cleanToken = cleanToken.substring(7).trim();
      }
      headers['Authorization'] = `Bearer ${cleanToken}`;
    }
  }

  const baseUrl = getApiBaseUrl();
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${normalizedPath}`, {
      ...options,
      headers,
    });
  } catch (err: any) {
    throw new APIError('SecureOps gateway is unavailable. Verify that the backend server is running.', 503);
  }

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { error: { message: response.statusText } };
    }

    const backendMsg = errorData?.error?.message;

    if (response.status === 401) {
      throw new APIError('Invalid API credential.', 401, errorData);
    } else if (response.status === 403) {
      throw new APIError(`Access Denied (RBAC / Tenant Violation): ${backendMsg || 'Permission denied'}`, 403, errorData);
    } else if (response.status === 429) {
      throw new APIError('Rate limit exceeded: Too many requests. Please wait.', 429, errorData);
    } else if (response.status === 503 || response.status === 502) {
      throw new APIError('SecureOps gateway is temporarily unavailable.', response.status, errorData);
    }

    throw new APIError(backendMsg || `HTTP ${response.status} Request Error`, response.status, errorData);
  }

  return response.json();
}

export const api = {
  getHealth: () => request<HealthResponse>('/health'),
  getReady: () => request<ReadinessResponse>('/ready'),

  processRequest: (userId: string, reqText: string, apiKey?: string) =>
    request<SecurityGatewayResponse>(
      '/v1/requests',
      {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, request: reqText }),
      },
      apiKey
    ),

  executeTool: (payload: { tool_name: string; tool_input: Record<string, any>; request_id?: string; user_id?: string; approval_id?: string }, apiKey?: string) =>
    request<ExecutionResponse>(
      '/v1/executions',
      {
        method: 'POST',
        body: JSON.stringify({
          request_id: payload.request_id || `req_fe_${Date.now()}`,
          user_id: payload.user_id || 'fe_operator',
          tool_name: payload.tool_name,
          tool_input: payload.tool_input,
          approval_id: payload.approval_id,
        }),
      },
      apiKey
    ),

  listApprovals: (statusFilter?: string) =>
    request<ApprovalsListResponse>(`/v1/approvals${statusFilter ? `?status=${statusFilter}` : ''}`),

  getApprovalDetail: (approvalId: string) => request<any>(`/v1/approvals/${approvalId}`),

  approveRequest: (approvalId: string, approverId: string) =>
    request<ApprovalActionResult>(`/v1/approvals/${approvalId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approver_id: approverId }),
    }),

  rejectRequest: (approvalId: string, approverId: string) =>
    request<ApprovalActionResult>(`/v1/approvals/${approvalId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ approver_id: approverId }),
    }),

  listAuditEvents: (params: { limit?: number; user_id?: string; request_id?: string; decision?: string } | number = 100) => {
    if (typeof params === 'number') {
      return request<AuditEventsResponse>(`/v1/audit/events?limit=${params}`);
    }
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.user_id) query.set('user_id', params.user_id);
    if (params?.request_id) query.set('request_id', params.request_id);
    if (params?.decision && params.decision !== 'ALL') query.set('decision', params.decision);
    const qStr = query.toString();
    return request<AuditEventsResponse>(`/v1/audit/events${qStr ? `?${qStr}` : ''}`);
  },

  listSecurityEvents: (limit: number = 50) => request<SecurityEventsResponse>(`/v1/security/events?limit=${limit}`),

  getDashboardSummary: (apiKey?: string) => request<DashboardSummaryResponse>('/v1/dashboard/summary', {}, apiKey),

  createCredential: (payload: { name: string; user_id?: string; role?: string }) =>
    request<CreateCredentialResponse>('/v1/credentials', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  revokeCredential: (credentialId: string) =>
    request<any>(`/v1/credentials/${credentialId}/revoke`, {
      method: 'POST',
    }),

  rotateCredential: (credentialId: string) =>
    request<any>(`/v1/credentials/${credentialId}/rotate`, {
      method: 'POST',
    }),
};
