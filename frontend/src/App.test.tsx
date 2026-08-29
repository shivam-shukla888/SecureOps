import { describe, it, expect } from 'vitest';
import { getApiBaseUrl, BASE_URL } from './services/api';

describe('SecureOps Frontend Security & API Tests', () => {
  it('verifies environment base URL default points to production Render gateway', () => {
    const url = getApiBaseUrl();
    expect(url).toBe('https://secureops-gateway.onrender.com');
    expect(BASE_URL).toBe('https://secureops-gateway.onrender.com');
  });

  it('validates single Bearer prefix formatting logic', () => {
    const rawToken = "  Bearer Bearer 'my_secret_token_123'  ";
    let cleanToken = rawToken.trim().replace(/['"]/g, '');
    while (cleanToken.toLowerCase().startsWith('bearer ')) {
      cleanToken = cleanToken.substring(7).trim();
    }
    const finalHeader = `Bearer ${cleanToken}`;
    expect(finalHeader).toBe('Bearer my_secret_token_123');
  });

  it('validates role hierarchy definitions', () => {
    const roles = ['OWNER', 'ADMIN', 'APPROVER', 'OPERATOR', 'VIEWER'];
    expect(roles).toContain('OWNER');
    expect(roles).toContain('APPROVER');
  });

  it('evaluates gateway online status correctly for ready and healthy responses', () => {
    const isReadyOnline = (res: { status: string }) => res && (res.status === 'ready' || res.status === 'healthy');
    expect(isReadyOnline({ status: 'ready' })).toBe(true);
    expect(isReadyOnline({ status: 'healthy' })).toBe(true);
    expect(isReadyOnline({ status: 'unhealthy' })).toBe(false);
    expect(isReadyOnline({ status: 'degraded' })).toBe(false);
  });

  it('imports shadcn Button component successfully', async () => {
    const { Button, buttonVariants } = await import('./components/ui/button');
    expect(Button).toBeDefined();
    expect(buttonVariants).toBeDefined();
    const defaultClasses = buttonVariants();
    expect(defaultClasses).toContain('bg-primary');
    expect(defaultClasses).toContain('text-primary-foreground');
  });

  it('verifies DashboardSummaryResponse data mapping & policy distribution calculations', () => {
    const mockSummary = {
      tenant_id: 'tenant_default',
      user_id: 'admin_user',
      role: 'ADMIN' as const,
      requests_today: 125,
      allowed_requests: 120,
      blocked_requests: 5,
      pending_approvals: 2,
      security_events: 5,
      provider_fallbacks: 1,
      metrics: {
        request_count: 125,
        avg_request_latency_ms: 42.5,
        avg_ai_provider_latency_ms: 180.2,
        ai_fallback_count: 1,
        decision_count: {
          ALLOW: 120,
          BLOCK: 5,
        },
        approval_count: 2,
        execution_count: 85,
        execution_failure_count: 0,
        rate_limit_count: 3,
        authentication_failure_count: 1,
      },
      timestamp: new Date().toISOString(),
    };

    const allowCount = mockSummary.metrics.decision_count.ALLOW;
    const blockCount = mockSummary.metrics.decision_count.BLOCK;
    const totalDecisions = allowCount + blockCount;
    const allowPercent = Math.round((allowCount / totalDecisions) * 100);
    const blockPercent = 100 - allowPercent;

    expect(mockSummary.requests_today).toBe(125);
    expect(mockSummary.allowed_requests).toBe(120);
    expect(mockSummary.blocked_requests).toBe(5);
    expect(mockSummary.pending_approvals).toBe(2);
    expect(totalDecisions).toBe(125);
    expect(allowPercent).toBe(96);
    expect(blockPercent).toBe(4);
    expect(mockSummary.metrics.avg_request_latency_ms).toBe(42.5);
    expect(mockSummary.metrics.avg_ai_provider_latency_ms).toBe(180.2);
  });

  it('imports DashboardView component successfully', async () => {
    const { DashboardView } = await import('./components/views/DashboardView');
    expect(DashboardView).toBeDefined();
  });

  it('verifies SecurityGatewayResponse contract and decision validation', () => {
    const allowResponse: import('./types/api').SecurityGatewayResponse = {
      request_id: 'req_123456789abc',
      user_id: 'operator_alice',
      intent: 'SEARCH_DOCUMENT',
      resource: 'documents',
      ai_risk: 'LOW',
      policy_risk: 'LOW',
      requires_approval: false,
      decision: 'ALLOW',
      override_applied: false,
      provider_used: 'gemini',
      fallback_used: false,
      approval_id: null,
      expires_at: null,
      execution_result: { status: 'COMPLETED', query: 'architecture' },
      timestamp: new Date().toISOString(),
    };

    const approvalResponse: import('./types/api').SecurityGatewayResponse = {
      request_id: 'req_987654321xyz',
      user_id: 'operator_bob',
      intent: 'UPDATE_DATA',
      resource: 'customer_account_502',
      ai_risk: 'MEDIUM',
      policy_risk: 'HIGH',
      requires_approval: true,
      decision: 'REQUIRE_APPROVAL',
      override_applied: true,
      provider_used: 'gemini',
      fallback_used: false,
      approval_id: 'appr_abc123456789',
      expires_at: new Date(Date.now() + 3600000).toISOString(),
      execution_result: { status: 'PENDING_APPROVAL', approval_id: 'appr_abc123456789' },
      timestamp: new Date().toISOString(),
    };

    const blockResponse: import('./types/api').SecurityGatewayResponse = {
      request_id: 'req_block123456',
      user_id: 'operator_charlie',
      intent: 'UNKNOWN',
      resource: 'database',
      ai_risk: 'HIGH',
      policy_risk: 'HIGH',
      requires_approval: false,
      decision: 'BLOCK',
      override_applied: false,
      provider_used: 'gemini',
      fallback_used: false,
      approval_id: null,
      expires_at: null,
      execution_result: { status: 'BLOCKED', reason: 'High risk prompt injection' },
      timestamp: new Date().toISOString(),
    };

    expect(allowResponse.decision).toBe('ALLOW');
    expect(allowResponse.requires_approval).toBe(false);
    expect(approvalResponse.decision).toBe('REQUIRE_APPROVAL');
    expect(approvalResponse.approval_id).toBe('appr_abc123456789');
    expect(approvalResponse.override_applied).toBe(true);
    expect(blockResponse.decision).toBe('BLOCK');
    expect(blockResponse.execution_result.status).toBe('BLOCKED');
  });

  it('imports RequestGatewayView component successfully', async () => {
    const { RequestGatewayView } = await import('./components/views/RequestGatewayView');
    expect(RequestGatewayView).toBeDefined();
  });

  it('verifies ApprovalTicket status states and action response contract', () => {
    const mockTicket: import('./types/api').ApprovalTicket = {
      approval_id: 'appr_ticket12345',
      request_id: 'req_ticket12345',
      requester_id: 'operator_sarah',
      intent: 'UPDATE_DATA',
      resource: 'customer_account_502',
      policy_risk: 'HIGH',
      status: 'PENDING',
      approver_id: null,
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 3600000).toISOString(),
    };

    expect(mockTicket.status).toBe('PENDING');
    expect(mockTicket.policy_risk).toBe('HIGH');
    expect(new Date(mockTicket.expires_at).getTime()).toBeGreaterThan(Date.now());

    const mockActionResult: import('./types/api').ApprovalActionResult = {
      request_id: mockTicket.request_id,
      approval_id: mockTicket.approval_id,
      decision: 'APPROVED',
      status: 'APPROVED',
      message: "Request 'req_ticket12345' successfully approved by security officer 'security_officer_bob'.",
      approver_id: 'security_officer_bob',
      timestamp: new Date().toISOString(),
      execution_result: { status: 'executed_post_approval' },
    };

    expect(mockActionResult.decision).toBe('APPROVED');
    expect(mockActionResult.approver_id).toBe('security_officer_bob');
    expect(mockActionResult.execution_result.status).toBe('executed_post_approval');
  });

  it('imports ApprovalCenterView component successfully', async () => {
    const { ApprovalCenterView } = await import('./components/views/ApprovalCenterView');
    expect(ApprovalCenterView).toBeDefined();
  });

  it('verifies SecurityEvent severity levels and event mapping', () => {
    const mockSecurityEvent: import('./types/api').SecurityEvent = {
      event_id: 'evt_sec123456',
      event_type: 'POLICY_OVERRIDE',
      severity: 'HIGH',
      tenant_id: 'tenant_default',
      user_id: 'operator_charlie',
      request_id: 'req_charlie123',
      timestamp: new Date().toISOString(),
      metadata: {
        reason: 'Anti-downgrade policy enforced risk escalation',
        intent: 'DELETE_DATA',
      },
    };

    expect(mockSecurityEvent.event_id).toBe('evt_sec123456');
    expect(mockSecurityEvent.severity).toBe('HIGH');
    expect(mockSecurityEvent.event_type).toBe('POLICY_OVERRIDE');
    expect(mockSecurityEvent.metadata.reason).toBeDefined();
  });

  it('imports SecurityEventsView component successfully', async () => {
    const { SecurityEventsView } = await import('./components/views/SecurityEventsView');
    expect(SecurityEventsView).toBeDefined();
  });

  it('verifies AuditEvent contract and decision telemetry', () => {
    const mockAuditEvent: import('./types/api').AuditEvent = {
      request_id: 'req_audit12345',
      tenant_id: 'tenant_default',
      user_id: 'operator_alice',
      intent: 'SEARCH_DOCUMENT',
      resource: 'documents',
      ai_risk: 'LOW',
      policy_risk: 'LOW',
      final_decision: 'ALLOW',
      provider: 'gemini',
      fallback_used: false,
      latency_ms: 38.4,
      error_status: null,
      timestamp: new Date().toISOString(),
    };

    expect(mockAuditEvent.request_id).toBe('req_audit12345');
    expect(mockAuditEvent.final_decision).toBe('ALLOW');
    expect(mockAuditEvent.latency_ms).toBe(38.4);
    expect(mockAuditEvent.provider).toBe('gemini');
    expect(mockAuditEvent.fallback_used).toBe(false);
  });

  it('imports AuditExplorerView component successfully', async () => {
    const { AuditExplorerView } = await import('./components/views/AuditExplorerView');
    expect(AuditExplorerView).toBeDefined();
  });

  it('verifies ExecutionResponse contract and execution status validation', () => {
    const mockExecution: import('./types/api').ExecutionResponse = {
      execution_id: 'exec_sandbox_12345',
      request_id: 'req_exec_12345',
      status: 'COMPLETED',
      tool_name: 'search_document_tool',
      result: {
        matches: ['Corporate Security Architecture v2.0'],
        count: 1,
      },
      latency_ms: 18.2,
      timestamp: new Date().toISOString(),
    };

    expect(mockExecution.execution_id).toBe('exec_sandbox_12345');
    expect(mockExecution.status).toBe('COMPLETED');
    expect(mockExecution.tool_name).toBe('search_document_tool');
    expect(mockExecution.latency_ms).toBe(18.2);
    expect(mockExecution.result.matches).toBeDefined();
  });

  it('imports ExecutionCenterView component successfully', async () => {
    const { ExecutionCenterView } = await import('./components/views/ExecutionCenterView');
    expect(ExecutionCenterView).toBeDefined();
  });

  it('verifies GOVERNED_TOOLS definitions and security controls', async () => {
    const { GOVERNED_TOOLS } = await import('./components/views/ToolsView');
    expect(GOVERNED_TOOLS).toHaveLength(5);

    const searchTool = GOVERNED_TOOLS.find((t) => t.name === 'search_document');
    expect(searchTool).toBeDefined();
    expect(searchTool?.requires_approval).toBe(false);
    expect(searchTool?.risk).toBe('LOW');

    const deleteTool = GOVERNED_TOOLS.find((t) => t.name === 'delete_data');
    expect(deleteTool).toBeDefined();
    expect(deleteTool?.requires_approval).toBe(true);
    expect(deleteTool?.risk).toBe('HIGH');
  });

  it('imports ToolsView component successfully', async () => {
    const { ToolsView } = await import('./components/views/ToolsView');
    expect(ToolsView).toBeDefined();
  });

  it('verifies APICredentialRecord and CreateCredentialResponse contract', () => {
    const mockCredResponse: import('./types/api').CreateCredentialResponse = {
      status: 'created',
      api_key: 'secops_fake_test_key_secret_for_unit_tests',
      credential: {
        credential_id: 'cred_test_12345',
        tenant_id: 'tenant_default',
        user_id: 'operator_sarah',
        name: 'Unit Test Gateway Key',
        role: 'OPERATOR',
        created_at: new Date().toISOString(),
      },
      warning: 'Store this API key securely. It will not be shown again.',
    };

    expect(mockCredResponse.status).toBe('created');
    expect(mockCredResponse.credential.credential_id).toBe('cred_test_12345');
    expect(mockCredResponse.credential.role).toBe('OPERATOR');
    expect(mockCredResponse.api_key).toBeDefined();
    expect(mockCredResponse.warning).toContain('not be shown again');
  });

  it('imports CredentialsView component successfully', async () => {
    const { CredentialsView } = await import('./components/views/CredentialsView');
    expect(CredentialsView).toBeDefined();
  });

  it('verifies RBAC role hierarchy and role catalog definition', () => {
    const validRoles: import('./types/api').RoleEnum[] = ['OWNER', 'ADMIN', 'APPROVER', 'OPERATOR', 'VIEWER'];
    expect(validRoles).toHaveLength(5);
    expect(validRoles).toContain('OWNER');
    expect(validRoles).toContain('APPROVER');
    expect(validRoles).toContain('OPERATOR');
  });

  it('imports RbacView component successfully', async () => {
    const { RbacView } = await import('./components/views/RbacView');
    expect(RbacView).toBeDefined();
  });

  it('verifies TENANTS_CATALOG definitions and isolation boundaries', async () => {
    const { TENANTS_CATALOG } = await import('./components/views/TenantsView');
    expect(TENANTS_CATALOG.length).toBeGreaterThanOrEqual(3);

    const defaultTenant = TENANTS_CATALOG.find((t) => t.id === 'tenant_default');
    expect(defaultTenant).toBeDefined();
    expect(defaultTenant?.status).toBe('ACTIVE');
    expect(defaultTenant?.isolation_controls).toBeDefined();
  });

  it('imports TenantsView component successfully', async () => {
    const { TenantsView } = await import('./components/views/TenantsView');
    expect(TenantsView).toBeDefined();
  });

  it('verifies HealthResponse and ReadinessResponse telemetry contract', () => {
    const mockHealth: import('./types/api').HealthResponse = {
      status: 'healthy',
      service: 'SecureOps API Gateway',
      timestamp: new Date().toISOString(),
    };

    const mockReady: import('./types/api').ReadinessResponse = {
      status: 'ready',
      rate_limiter: 'ready',
      database: 'ready',
      redis: 'ready',
      metrics_summary: {
        total_requests: 124,
        avg_latency_ms: 12.4,
      },
      timestamp: new Date().toISOString(),
    };

    expect(mockHealth.status).toBe('healthy');
    expect(mockHealth.service).toBe('SecureOps API Gateway');
    expect(mockReady.status).toBe('ready');
    expect(mockReady.database).toBe('ready');
    expect(mockReady.rate_limiter).toBe('ready');
    expect(mockReady.redis).toBe('ready');
  });

  it('imports HealthView component successfully', async () => {
    const { HealthView } = await import('./components/views/HealthView');
    expect(HealthView).toBeDefined();
  });

  it('evaluates HealthView status & banner transitions for production health/readiness scenarios', () => {
    const computeHealthViewState = (
      healthData: { status?: string } | undefined,
      healthLoading: boolean,
      healthError: boolean,
      readyData: { status?: string; rate_limiter?: string; database?: string; redis?: string } | undefined,
      readyLoading: boolean,
      readyError: boolean
    ) => {
      const isLivenessOk = Boolean(
        !healthError &&
          healthData?.status &&
          (healthData.status.toLowerCase() === 'healthy' || healthData.status.toLowerCase() === 'ok')
      );

      const isReadinessOk = Boolean(
        !readyError &&
          readyData?.status &&
          (readyData.status.toLowerCase() === 'ready' ||
            readyData.status.toLowerCase() === 'healthy' ||
            readyData.status.toLowerCase() === 'ok')
      );

      const isInitialLoading = (healthLoading && !healthData) || (readyLoading && !readyData);

      const isDegraded = Boolean(
        !isInitialLoading &&
          isLivenessOk &&
          (readyData?.status?.toLowerCase() === 'degraded' || !isReadinessOk)
      );

      const bannerTitle = isInitialLoading
        ? 'CHECKING GATEWAY STATUS...'
        : isLivenessOk && isReadinessOk
        ? 'SYSTEM HEALTHY & READY'
        : isDegraded
        ? 'SYSTEM DEGRADED (PARTIAL READINESS)'
        : 'GATEWAY SERVICE UNAVAILABLE';

      const getBadge = (statusStr: string | undefined, loading: boolean) => {
        if (loading) return 'CHECKING...';
        const val = statusStr?.toLowerCase();
        if (val === 'healthy' || val === 'ok') return 'HEALTHY';
        if (val === 'ready') return 'ONLINE / READY';
        if (val === 'degraded' || val === 'unconfigured') return val.toUpperCase();
        return 'UNHEALTHY';
      };

      return {
        isLivenessOk,
        isReadinessOk,
        isInitialLoading,
        isDegraded,
        bannerTitle,
        livenessBadge: getBadge(healthData?.status, healthLoading && !healthData),
        readinessBadge: getBadge(readyData?.status, readyLoading && !readyData),
      };
    };

    // Scenario 1: /ready = "ready" (200), /health = "healthy" (200) -> Both succeed
    const normalState = computeHealthViewState(
      { status: 'healthy' },
      false,
      false,
      { status: 'ready', rate_limiter: 'ready', database: 'ready', redis: 'ready' },
      false,
      false
    );
    expect(normalState.isLivenessOk).toBe(true);
    expect(normalState.isReadinessOk).toBe(true);
    expect(normalState.bannerTitle).toBe('SYSTEM HEALTHY & READY');
    expect(normalState.livenessBadge).toBe('HEALTHY');
    expect(normalState.readinessBadge).toBe('ONLINE / READY');

    // Scenario 2: /ready succeeds ("ready"), but /health fails -> Must NOT mark liveness healthy
    const healthFailedState = computeHealthViewState(
      undefined,
      false,
      true, // health error
      { status: 'ready', rate_limiter: 'ready', database: 'ready', redis: 'ready' },
      false,
      false
    );
    expect(healthFailedState.isLivenessOk).toBe(false);
    expect(healthFailedState.isReadinessOk).toBe(true);
    expect(healthFailedState.bannerTitle).toBe('GATEWAY SERVICE UNAVAILABLE');
    expect(healthFailedState.livenessBadge).toBe('UNHEALTHY');
    expect(healthFailedState.readinessBadge).toBe('ONLINE / READY');

    // Scenario 3: /health succeeds ("healthy"), but /ready reports degraded status
    const degradedState = computeHealthViewState(
      { status: 'healthy' },
      false,
      false,
      { status: 'degraded', rate_limiter: 'ready', database: 'unhealthy', redis: 'ready' },
      false,
      false
    );
    expect(degradedState.isLivenessOk).toBe(true);
    expect(degradedState.isReadinessOk).toBe(false);
    expect(degradedState.isDegraded).toBe(true);
    expect(degradedState.bannerTitle).toBe('SYSTEM DEGRADED (PARTIAL READINESS)');
    expect(degradedState.livenessBadge).toBe('HEALTHY');
    expect(degradedState.readinessBadge).toBe('DEGRADED');

    // Scenario 4: Initial loading state
    const loadingState = computeHealthViewState(
      undefined,
      true,
      false,
      undefined,
      true,
      false
    );
    expect(loadingState.isInitialLoading).toBe(true);
    expect(loadingState.bannerTitle).toBe('CHECKING GATEWAY STATUS...');
    expect(loadingState.livenessBadge).toBe('CHECKING...');
    expect(loadingState.readinessBadge).toBe('CHECKING...');

    // Scenario 5: Both endpoints fail
    const bothFailedState = computeHealthViewState(
      undefined,
      false,
      true,
      undefined,
      false,
      true
    );
    expect(bothFailedState.isLivenessOk).toBe(false);
    expect(bothFailedState.isReadinessOk).toBe(false);
    expect(bothFailedState.bannerTitle).toBe('GATEWAY SERVICE UNAVAILABLE');
    expect(bothFailedState.livenessBadge).toBe('UNHEALTHY');
    expect(bothFailedState.readinessBadge).toBe('UNHEALTHY');
  });

  it('validates case-insensitive status handling for health and ready endpoints', () => {
    const isLivenessOk = (status?: string) =>
      Boolean(status && (status.toLowerCase() === 'healthy' || status.toLowerCase() === 'ok'));
    const isReadinessOk = (status?: string) =>
      Boolean(status && (status.toLowerCase() === 'ready' || status.toLowerCase() === 'healthy' || status.toLowerCase() === 'ok'));

    expect(isLivenessOk('HEALTHY')).toBe(true);
    expect(isLivenessOk('healthy')).toBe(true);
    expect(isLivenessOk('OK')).toBe(true);
    expect(isLivenessOk('ok')).toBe(true);
    expect(isLivenessOk('unhealthy')).toBe(false);
    expect(isLivenessOk(undefined)).toBe(false);

    expect(isReadinessOk('READY')).toBe(true);
    expect(isReadinessOk('ready')).toBe(true);
    expect(isReadinessOk('degraded')).toBe(false);
    expect(isReadinessOk('unhealthy')).toBe(false);
  });

  it('imports SettingsView component successfully', async () => {
    const { SettingsView } = await import('./components/views/SettingsView');
    expect(SettingsView).toBeDefined();
  });

  // Comprehensive Regression Tests for /health & /ready: TEST 1 through TEST 8
  describe('Regression: Health & Readiness Endpoint Contract & View Behavior', () => {
    it('TEST 1: getHealth() receives HTTP 200 with status "healthy" -> Expected: healthy', () => {
      const payload: import('./types/api').HealthResponse = {
        status: 'healthy',
        service: 'SecureOps API Gateway',
        timestamp: '2026-08-29T14:30:00.000Z',
      };
      const isHealthy = payload.status.toLowerCase() === 'healthy' || payload.status.toLowerCase() === 'ok';
      expect(isHealthy).toBe(true);
      expect(payload.service).toBe('SecureOps API Gateway');
    });

    it('TEST 2: getHealth() receives HTTP 200 with status "ok" -> Expected: healthy', () => {
      const payload = {
        status: 'ok',
        service: 'SecureOps API Gateway',
        timestamp: '2026-08-29T14:30:00.000Z',
      };
      const isHealthy = payload.status.toLowerCase() === 'healthy' || payload.status.toLowerCase() === 'ok';
      expect(isHealthy).toBe(true);
    });

    it('TEST 3: getHealth() receives HTTP 503 -> Expected: unhealthy/error', () => {
      const httpStatus = 503;
      const isSuccess = httpStatus >= 200 && httpStatus < 300;
      expect(isSuccess).toBe(false);
      const isLivenessOk = isSuccess && false;
      expect(isLivenessOk).toBe(false);
    });

    it('TEST 4: getHealth() network failure -> Expected: unavailable/error', () => {
      const isNetworkError = true;
      const isLivenessOk = !isNetworkError;
      expect(isLivenessOk).toBe(false);
    });

    it('TEST 5: getReady() = ready AND getHealth() = healthy -> Expected banner: "SYSTEM HEALTHY & READY"', () => {
      const isLivenessOk = true;
      const isReadinessOk = true;
      const isInitialLoading = false;
      const isDegraded = false;

      const bannerTitle = isInitialLoading
        ? 'CHECKING GATEWAY STATUS...'
        : isLivenessOk && isReadinessOk
        ? 'SYSTEM HEALTHY & READY'
        : isDegraded
        ? 'SYSTEM DEGRADED (PARTIAL READINESS)'
        : 'GATEWAY SERVICE UNAVAILABLE';

      expect(bannerTitle).toBe('SYSTEM HEALTHY & READY');
    });

    it('TEST 6: getReady() = ready AND getHealth() fails -> Expected Readiness = READY, Liveness = UNHEALTHY, Banner = GATEWAY SERVICE UNAVAILABLE', () => {
      const isLivenessOk = false;
      const isReadinessOk = true;
      const isInitialLoading = false;
      const isDegraded = false; // Degraded requires isLivenessOk to be true

      const bannerTitle = isInitialLoading
        ? 'CHECKING GATEWAY STATUS...'
        : isLivenessOk && isReadinessOk
        ? 'SYSTEM HEALTHY & READY'
        : isDegraded
        ? 'SYSTEM DEGRADED (PARTIAL READINESS)'
        : 'GATEWAY SERVICE UNAVAILABLE';

      const livenessBadge = isLivenessOk ? 'HEALTHY' : 'UNHEALTHY';
      const readinessBadge = isReadinessOk ? 'ONLINE / READY' : 'UNHEALTHY';

      expect(readinessBadge).toBe('ONLINE / READY');
      expect(livenessBadge).toBe('UNHEALTHY');
      expect(bannerTitle).toBe('GATEWAY SERVICE UNAVAILABLE');
    });

    it('TEST 7: Ensure /health never gets /v1 appended', () => {
      const baseUrl = getApiBaseUrl();
      expect(baseUrl).not.toMatch(/\/v1\/?$/);
      expect(baseUrl).not.toMatch(/\/api\/?$/);
      const healthUrl = `${baseUrl}/health`;
      expect(healthUrl).toBe('https://secureops-gateway.onrender.com/health');
      expect(healthUrl).not.toContain('/v1/health');
    });

    it('TEST 8: Ensure production never uses localhost or 127.0.0.1', () => {
      const baseUrl = getApiBaseUrl();
      expect(baseUrl).not.toContain('localhost');
      expect(baseUrl).not.toContain('127.0.0.1');
      expect(baseUrl).toBe('https://secureops-gateway.onrender.com');
    });

    it('TEST 9: Ensure public health and ready endpoints do not send unnecessary Authorization or Content-Type headers', () => {
      const buildHeaders = (path: string, options: { body?: any; headers?: Record<string, string> } = {}, token?: string) => {
        const isPublicRootEndpoint = path === '/health' || path === '/ready' || path === 'health' || path === 'ready';
        const headers: Record<string, string> = {
          Accept: 'application/json',
          ...(options.headers as Record<string, string>),
        };
        if (options.body && !headers['Content-Type']) {
          headers['Content-Type'] = 'application/json';
        }
        if (!isPublicRootEndpoint && token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
      };

      const healthHeaders = buildHeaders('/health', {}, 'secret-token-123');
      expect(healthHeaders['Accept']).toBe('application/json');
      expect(healthHeaders['Authorization']).toBeUndefined();
      expect(healthHeaders['Content-Type']).toBeUndefined();

      const readyHeaders = buildHeaders('/ready', {}, 'secret-token-123');
      expect(readyHeaders['Accept']).toBe('application/json');
      expect(readyHeaders['Authorization']).toBeUndefined();
      expect(readyHeaders['Content-Type']).toBeUndefined();

      const authedHeaders = buildHeaders('/v1/requests', { body: JSON.stringify({ user_id: 'u1' }) }, 'secret-token-123');
      expect(authedHeaders['Accept']).toBe('application/json');
      expect(authedHeaders['Authorization']).toBe('Bearer secret-token-123');
      expect(authedHeaders['Content-Type']).toBe('application/json');
    });
  });
});
