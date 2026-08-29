import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Zap,
  CheckCircle2,
  XCircle,
  Sparkles,
  Cpu,
  Database,
  RefreshCw,
  AlertTriangle,
  Server,
  Layers,
  FileText,
  Lock,
} from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

export const DashboardView: React.FC = () => {
  const { tenantId, userRole } = useAuth();

  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
    refetch: refetchSummary,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ['dashboardSummary'],
    queryFn: () => api.getDashboardSummary(),
    refetchInterval: 10000,
  });

  const { data: readiness, refetch: refetchReadiness } = useQuery({
    queryKey: ['systemReadiness'],
    queryFn: () => api.getReady(),
    refetchInterval: 15000,
  });

  const handleRefresh = () => {
    refetchSummary();
    refetchReadiness();
  };

  const allowCount =
    summary?.metrics?.decision_count?.ALLOW ?? summary?.allowed_requests ?? 0;
  const blockCount =
    summary?.metrics?.decision_count?.BLOCK ?? summary?.blocked_requests ?? 0;
  const totalDecisions = allowCount + blockCount;
  const allowPercent =
    totalDecisions > 0 ? Math.round((allowCount / totalDecisions) * 100) : 100;
  const blockPercent = totalDecisions > 0 ? 100 - allowPercent : 0;

  const formattedLastUpdated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString()
    : summary?.timestamp
    ? new Date(summary.timestamp).toLocaleTimeString()
    : 'Live';

  return (
    <div className="space-y-6 select-none">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-white tracking-tight font-mono uppercase">
              SECURITY COMMAND CENTER
            </h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              LIVE
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Real-time visibility into AI gateway activity, policy decisions and security posture.
          </p>
        </div>

        {/* Metadata & Refresh Bar */}
        <div className="flex items-center gap-3 self-start md:self-auto">
          <div className="hidden lg:flex items-center gap-3 px-3 py-1.5 rounded-lg bg-[#111827] border border-slate-800 text-[11px] font-mono text-slate-400">
            <span>
              Tenant: <strong className="text-slate-200">{summary?.tenant_id || tenantId}</strong>
            </span>
            <span className="text-slate-700">|</span>
            <span>
              Role: <strong className="text-cyan-400">{summary?.role || userRole}</strong>
            </span>
            <span className="text-slate-700">|</span>
            <span>
              Updated: <strong className="text-slate-200">{formattedLastUpdated}</strong>
            </span>
          </div>

          <button
            onClick={handleRefresh}
            className="px-3 py-1.5 rounded-lg bg-[#111827] border border-slate-800 hover:border-cyan-500/40 text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1.5 transition-colors cursor-pointer"
            title="Refresh dashboard metrics"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Error State */}
      {summaryError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
            <span className="text-xs font-mono">
              Unable to reach SecureOps telemetry service. Verifying gateway connection...
            </span>
          </div>
          <button
            onClick={() => refetchSummary()}
            className="px-3 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 text-xs font-mono text-rose-200 border border-rose-500/30"
          >
            Retry
          </button>
        </div>
      )}

      {/* Primary 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Requests Today */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 hover:border-slate-700/80 transition-colors flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400">Requests Today</span>
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white font-mono tracking-tight">
              {summaryLoading ? '...' : (summary?.requests_today ?? 0).toLocaleString()}
            </div>
            <div className="mt-2 text-[11px] text-slate-500 font-mono flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              <span>Monitored via Gateway</span>
            </div>
          </div>
        </div>

        {/* Card 2: Allowed Requests */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 hover:border-emerald-500/30 transition-colors flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400">Allowed Requests</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-emerald-400 font-mono tracking-tight">
              {summaryLoading ? '...' : (summary?.allowed_requests ?? 0).toLocaleString()}
            </div>
            <div className="mt-2 text-[11px] text-slate-500 font-mono flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Passed Security Policy</span>
            </div>
          </div>
        </div>

        {/* Card 3: Blocked Requests */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 hover:border-rose-500/30 transition-colors flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400">Blocked Requests</span>
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <XCircle className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-rose-400 font-mono tracking-tight">
              {summaryLoading ? '...' : (summary?.blocked_requests ?? 0).toLocaleString()}
            </div>
            <div className="mt-2 text-[11px] text-slate-500 font-mono flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
              <span>Policy Engine Enforced</span>
            </div>
          </div>
        </div>

        {/* Card 4: Pending Approvals */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 hover:border-amber-500/30 transition-colors flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400">Pending Approvals</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-amber-400 font-mono tracking-tight">
              {summaryLoading ? '...' : (summary?.pending_approvals ?? 0).toLocaleString()}
            </div>
            <div className="mt-2 text-[11px] text-slate-500 font-mono flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-amber-400" />
              <span>Awaiting Security Officer</span>
            </div>
          </div>
        </div>
      </div>

      {/* Secondary Security Overview (4 sub-metrics) */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {/* Security Events */}
        <div className="p-4 rounded-xl bg-[#0e1422] border border-slate-800/80">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-mono mb-1">
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            <span>Security Events</span>
          </div>
          <div className="text-lg font-bold text-white font-mono">
            {summaryLoading ? '...' : summary?.security_events ?? 0}
          </div>
        </div>

        {/* Provider Fallbacks */}
        <div className="p-4 rounded-xl bg-[#0e1422] border border-slate-800/80">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-mono mb-1">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>Provider Fallbacks</span>
          </div>
          <div className="text-lg font-bold text-white font-mono">
            {summaryLoading ? '...' : summary?.provider_fallbacks ?? summary?.metrics?.ai_fallback_count ?? 0}
          </div>
        </div>

        {/* Average Request Latency */}
        <div className="p-4 rounded-xl bg-[#0e1422] border border-slate-800/80">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-mono mb-1">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>Avg Request Latency</span>
          </div>
          <div className="text-lg font-bold text-white font-mono">
            {summaryLoading
              ? '...'
              : summary?.metrics?.avg_request_latency_ms !== undefined
              ? `${summary.metrics.avg_request_latency_ms.toFixed(1)} ms`
              : '0.0 ms'}
          </div>
        </div>

        {/* AI Provider Latency */}
        <div className="p-4 rounded-xl bg-[#0e1422] border border-slate-800/80">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-mono mb-1">
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
            <span>AI Provider Latency</span>
          </div>
          <div className="text-lg font-bold text-white font-mono">
            {summaryLoading
              ? '...'
              : summary?.metrics?.avg_ai_provider_latency_ms !== undefined
              ? `${summary.metrics.avg_ai_provider_latency_ms.toFixed(1)} ms`
              : '0.0 ms'}
          </div>
        </div>
      </div>

      {/* Main Two-Column Telemetry Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Security Decision Distribution */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-semibold text-white font-mono uppercase">
                Policy Decision Distribution
              </h2>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Total Decisions: <strong className="text-slate-200">{totalDecisions}</strong>
            </span>
          </div>

          {/* Decision Bar Visualization */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-emerald-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                ALLOW: {allowCount} ({allowPercent}%)
              </span>
              <span className="text-rose-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-rose-400" />
                BLOCK: {blockCount} ({blockPercent}%)
              </span>
            </div>

            {/* Segmented CSS Progress Bar */}
            <div className="h-3 w-full bg-slate-900 rounded-full overflow-hidden flex border border-slate-800">
              <div
                style={{ width: `${allowPercent}%` }}
                className="h-full bg-emerald-500 transition-all duration-500"
                title={`Allowed: ${allowCount}`}
              />
              <div
                style={{ width: `${blockPercent}%` }}
                className="h-full bg-rose-500 transition-all duration-500"
                title={`Blocked: ${blockCount}`}
              />
            </div>
          </div>

          {/* Detailed Decision Counts */}
          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800">
              <div className="text-[11px] text-slate-400 font-mono">Autonomous ALLOW</div>
              <div className="text-xl font-bold text-emerald-400 font-mono mt-1">
                {allowCount}
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-1">
                Zero security risk detected
              </div>
            </div>

            <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800">
              <div className="text-[11px] text-slate-400 font-mono">Enforced BLOCK</div>
              <div className="text-xl font-bold text-rose-400 font-mono mt-1">
                {blockCount}
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-1">
                High risk / prompt injection
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Infrastructure Liveness */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-semibold text-white font-mono uppercase">
                Infrastructure Readiness
              </h2>
            </div>
            <span className="text-[11px] font-mono text-emerald-400">
              {readiness?.status === 'ready' ? 'ALL SYSTEMS OPERATIONAL' : 'SYSTEM DEGRADED'}
            </span>
          </div>

          <div className="space-y-2.5">
            {/* Sliding Window Rate Limiter */}
            <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Activity className="w-4 h-4 text-cyan-400 shrink-0" />
                <div>
                  <div className="text-xs font-semibold text-slate-200">Sliding Window Rate Limiter</div>
                  <div className="text-[10px] text-slate-400 font-mono">In-Memory / Redis Backend</div>
                </div>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono uppercase">
                {readiness?.rate_limiter || 'READY'}
              </span>
            </div>

            {/* PostgreSQL Persistence */}
            <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Database className="w-4 h-4 text-emerald-400 shrink-0" />
                <div>
                  <div className="text-xs font-semibold text-slate-200">PostgreSQL Data Store</div>
                  <div className="text-[10px] text-slate-400 font-mono">Partitioned Audits & Credentials</div>
                </div>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono uppercase">
                {readiness?.database || 'READY'}
              </span>
            </div>

            {/* Gateway Liveness */}
            <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ShieldCheck className="w-4 h-4 text-purple-400 shrink-0" />
                <div>
                  <div className="text-xs font-semibold text-slate-200">AI Gateway Core Engine</div>
                  <div className="text-[10px] text-slate-400 font-mono">Policy Enforcement & Telemetry</div>
                </div>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono uppercase">
                {readiness?.status || 'READY'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row: Normal Activity vs Security Failures */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Normal Operations Activity */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <FileText className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-semibold text-slate-200 font-mono uppercase">
              Normal Operations Telemetry
            </h3>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800">
              <span className="text-[10px] text-slate-500 font-mono block">Request Volume</span>
              <strong className="text-base font-mono text-slate-200 mt-1 block">
                {summary?.metrics?.request_count ?? summary?.requests_today ?? 0}
              </strong>
            </div>
            <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800">
              <span className="text-[10px] text-slate-500 font-mono block">Approvals Handled</span>
              <strong className="text-base font-mono text-slate-200 mt-1 block">
                {summary?.metrics?.approval_count ?? 0}
              </strong>
            </div>
            <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800">
              <span className="text-[10px] text-slate-500 font-mono block">Tool Executions</span>
              <strong className="text-base font-mono text-slate-200 mt-1 block">
                {summary?.metrics?.execution_count ?? 0}
              </strong>
            </div>
          </div>
        </div>

        {/* Security Events & Failures */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <h3 className="text-xs font-semibold text-slate-200 font-mono uppercase">
              Security Events & Failures
            </h3>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800">
              <span className="text-[10px] text-slate-500 font-mono block">Execution Failures</span>
              <strong className="text-base font-mono text-rose-400 mt-1 block">
                {summary?.metrics?.execution_failure_count ?? 0}
              </strong>
            </div>
            <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800">
              <span className="text-[10px] text-slate-500 font-mono block">Rate Throttles</span>
              <strong className="text-base font-mono text-amber-400 mt-1 block">
                {summary?.metrics?.rate_limit_count ?? 0}
              </strong>
            </div>
            <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800">
              <span className="text-[10px] text-slate-500 font-mono block">Auth Failures</span>
              <strong className="text-base font-mono text-rose-400 mt-1 block">
                {summary?.metrics?.authentication_failure_count ?? 0}
              </strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
