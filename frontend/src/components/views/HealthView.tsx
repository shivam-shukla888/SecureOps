import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Database,
  Cpu,
  RefreshCw,
  Server,
  Layers,
  ShieldCheck,
  Zap,
  Info,
  Clock,
} from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

export const HealthView: React.FC = () => {
  const { tenantId, userRole } = useAuth();

  const {
    data: health,
    isLoading: healthLoading,
    isError: healthError,
    refetch: refetchHealth,
  } = useQuery({
    queryKey: ['systemHealthLiveness'],
    queryFn: () => api.getHealth(),
    refetchInterval: 10000,
    retry: 2,
    staleTime: 5000,
  });

  const {
    data: ready,
    isLoading: readyLoading,
    isError: readyError,
    error: readyFetchError,
    refetch: refetchReady,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ['systemHealthReadiness'],
    queryFn: () => api.getReady(),
    refetchInterval: 10000,
    retry: 2,
    staleTime: 5000,
  });

  const handleManualRefresh = () => {
    refetchHealth();
    refetchReady();
  };

  const isLivenessOk = Boolean(
    !healthError &&
      health?.status &&
      (health.status.toLowerCase() === 'healthy' || health.status.toLowerCase() === 'ok')
  );

  const isReadinessOk = Boolean(
    !readyError &&
      ready?.status &&
      (ready.status.toLowerCase() === 'ready' ||
        ready.status.toLowerCase() === 'healthy' ||
        ready.status.toLowerCase() === 'ok')
  );

  const isInitialLoading = (healthLoading && !health) || (readyLoading && !ready);

  const isDegraded = Boolean(
    !isInitialLoading &&
      isLivenessOk &&
      (ready?.status?.toLowerCase() === 'degraded' || !isReadinessOk)
  );

  const getStatusBadge = (statusStr: string | undefined, loading: boolean) => {
    if (loading) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700 animate-pulse shrink-0">
          CHECKING...
        </span>
      );
    }
    const val = statusStr?.toLowerCase();
    if (val === 'healthy' || val === 'ok') {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 inline-flex items-center gap-1 shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          HEALTHY
        </span>
      );
    }
    if (val === 'ready') {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 inline-flex items-center gap-1 shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          ONLINE / READY
        </span>
      );
    }
    if (val === 'degraded' || val === 'unconfigured') {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 inline-flex items-center gap-1 shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          {val.toUpperCase()}
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 inline-flex items-center gap-1 shrink-0">
        <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
        UNHEALTHY
      </span>
    );
  };

  const formattedLastChecked = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString()
    : 'Live';

  return (
    <div className="space-y-4 sm:space-y-6 select-none font-mono text-xs max-w-full">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 pb-2 border-b border-slate-800/80">
        <div className="min-w-0">
          <div className="flex items-center gap-2 sm:gap-2.5 flex-wrap">
            <h1 className="text-lg sm:text-xl font-bold text-white tracking-tight uppercase truncate">
              SYSTEM HEALTH
            </h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shrink-0">
              INFRASTRUCTURE TELEMETRY
            </span>
          </div>
          <p className="text-[11px] sm:text-xs text-slate-400 mt-1">
            Monitor SecureOps gateway liveness and infrastructure readiness.
          </p>
        </div>

        <div className="flex items-center gap-2 sm:gap-3 self-start sm:self-auto shrink-0">
          <div className="flex items-center gap-2 sm:gap-3 px-2.5 sm:px-3 py-1.5 rounded-lg bg-[#111827] border border-slate-800 text-[10px] sm:text-[11px] text-slate-400">
            <span>
              Checked: <strong className="text-slate-200">{formattedLastChecked}</strong>
            </span>
            <span className="text-slate-700">|</span>
            <span>
              Tenant: <strong className="text-cyan-400">{tenantId}</strong>
            </span>
          </div>

          <button
            onClick={handleManualRefresh}
            className="px-3 py-2 sm:py-1.5 min-h-[44px] sm:min-h-0 rounded-lg bg-[#111827] border border-slate-800 hover:border-cyan-500/40 text-xs text-cyan-400 hover:text-cyan-300 flex items-center justify-center gap-1.5 transition-colors cursor-pointer shrink-0"
            title="Re-query health endpoints"
            aria-label="Re-query health endpoints"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Re-Check</span>
          </button>
        </div>
      </div>

      {/* Primary Gateway Status Summary Card */}
      <div
        className={`p-4 sm:p-5 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-3 sm:gap-4 ${
          isInitialLoading
            ? 'bg-slate-900/40 border-slate-800 text-slate-300'
            : isLivenessOk && isReadinessOk
            ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
            : isDegraded
            ? 'bg-amber-950/20 border-amber-500/40 text-amber-300'
            : 'bg-rose-950/20 border-rose-500/40 text-rose-300'
        }`}
      >
        <div className="space-y-1 min-w-0">
          <div className="text-[10px] tracking-wider uppercase text-slate-400">
            OPERATIONAL STATUS
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {isInitialLoading ? (
              <RefreshCw className="w-5 sm:w-6 h-5 sm:h-6 text-cyan-400 animate-spin shrink-0" />
            ) : isLivenessOk && isReadinessOk ? (
              <CheckCircle2 className="w-5 sm:w-6 h-5 sm:h-6 text-emerald-400 shrink-0" />
            ) : isDegraded ? (
              <AlertTriangle className="w-5 sm:w-6 h-5 sm:h-6 text-amber-400 shrink-0" />
            ) : (
              <XCircle className="w-5 sm:w-6 h-5 sm:h-6 text-rose-400 shrink-0" />
            )}
            <h2 className="text-base sm:text-xl font-bold tracking-tight uppercase break-words">
              {isInitialLoading
                ? 'CHECKING GATEWAY STATUS...'
                : isLivenessOk && isReadinessOk
                ? 'SYSTEM HEALTHY & READY'
                : isDegraded
                ? 'SYSTEM DEGRADED (PARTIAL READINESS)'
                : 'GATEWAY SERVICE UNAVAILABLE'}
            </h2>
          </div>
          <p className="text-xs text-slate-300 font-sans break-words">
            {isInitialLoading
              ? 'Probing gateway liveness (/health) and infrastructure readiness (/ready)...'
              : isLivenessOk && isReadinessOk
              ? 'All core services and infrastructure dependencies are operational.'
              : isDegraded
              ? 'Gateway process is responding, but one or more dependencies report degraded status.'
              : 'Unable to reach backend gateway process. Check deployment status.'}
          </p>
        </div>

        <div className="md:text-right text-xs shrink-0 space-y-1 pt-2 md:pt-0 border-t md:border-t-0 border-slate-800">
          <span className="text-slate-400 block text-[10px]">SERVICE NAME</span>
          <span className="font-bold text-white block">
            {health?.service || 'SecureOps API Gateway'}
          </span>
          <span className="text-[10px] text-slate-500 block">
            {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : '--'}
          </span>
        </div>
      </div>

      {/* Liveness vs Readiness Architecture Explanation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
        {/* Liveness Panel */}
        <div className="p-4 rounded-xl bg-[#111827] border border-slate-800/80 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2 gap-2 flex-wrap">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400 shrink-0" />
              <h3 className="text-xs font-semibold text-white uppercase">
                Application Liveness (/health)
              </h3>
            </div>
            {getStatusBadge(health?.status, healthLoading && !health)}
          </div>
          <p className="text-[11px] text-slate-400 font-sans">
            Confirms the HTTP gateway process is active, responding to probes, and serving requests.
          </p>
          <div className="p-2.5 rounded bg-[#0e1422] border border-slate-800 text-[11px] space-y-1">
            <div className="flex justify-between gap-2">
              <span className="text-slate-500">Service:</span>
              <strong className="text-slate-300 text-right">{health?.service || 'SecureOps API Gateway'}</strong>
            </div>
            <div className="flex justify-between gap-2">
              <span className="text-slate-500">Server Time:</span>
              <span className="text-slate-400 select-all text-right break-all">
                {health?.timestamp || '--'}
              </span>
            </div>
          </div>
        </div>

        {/* Readiness Panel */}
        <div className="p-4 rounded-xl bg-[#111827] border border-slate-800/80 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2 gap-2 flex-wrap">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-cyan-400 shrink-0" />
              <h3 className="text-xs font-semibold text-white uppercase">
                Infrastructure Readiness (/ready)
              </h3>
            </div>
            {getStatusBadge(ready?.status, readyLoading && !ready)}
          </div>
          <p className="text-[11px] text-slate-400 font-sans">
            Confirms essential backend components (PostgreSQL database, Redis cache, Rate Limiter) are available to safely process traffic.
          </p>
          <div className="p-2.5 rounded bg-[#0e1422] border border-slate-800 text-[11px] space-y-1">
            <div className="flex justify-between gap-2">
              <span className="text-slate-500">Readiness Status:</span>
              <strong className="text-cyan-300 uppercase text-right">{ready?.status || 'CHECKING'}</strong>
            </div>
            <div className="flex justify-between gap-2">
              <span className="text-slate-500">Last Verified:</span>
              <span className="text-slate-400 select-all text-right break-all">
                {ready?.timestamp || '--'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Infrastructure Dependency Component Cards */}
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <h3 className="text-xs font-semibold text-white uppercase flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>Infrastructure Components (3 Probed Dependencies)</span>
          </h3>
          <span className="text-[10px] text-slate-500">Live Backend Verification</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
          {/* Rate Limiter */}
          <div className="p-4 rounded-xl bg-[#111827] border border-slate-800/80 space-y-3 flex flex-col justify-between">
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-cyan-400 shrink-0" />
                  <strong className="text-white text-xs">Rate Limiter</strong>
                </div>
                {getStatusBadge(ready?.rate_limiter, readyLoading && !ready)}
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Sliding-window token bucket enforcement engine tracking tenant and user request quotas.
              </p>
            </div>
            <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
              <span>Scope</span>
              <span className="text-slate-300">tenant_id : user_id</span>
            </div>
          </div>

          {/* PostgreSQL Database */}
          <div className="p-4 rounded-xl bg-[#111827] border border-slate-800/80 space-y-3 flex flex-col justify-between">
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-cyan-400 shrink-0" />
                  <strong className="text-white text-xs">PostgreSQL Database</strong>
                </div>
                {getStatusBadge(ready?.database, readyLoading && !ready)}
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Primary persistent store for credentials, security logs, and tenant partition records.
              </p>
            </div>
            <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
              <span>Storage</span>
              <span className="text-slate-300">Supabase / PostgreSQL</span>
            </div>
          </div>

          {/* Redis Cache */}
          <div className="p-4 rounded-xl bg-[#111827] border border-slate-800/80 space-y-3 flex flex-col justify-between sm:col-span-2 lg:col-span-1">
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-cyan-400 shrink-0" />
                  <strong className="text-white text-xs">Redis Distributed State</strong>
                </div>
                {getStatusBadge(ready?.redis, readyLoading && !ready)}
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Distributed in-memory store for idempotency keys, shared rate-limit windows, and session cache.
              </p>
            </div>
            <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
              <span>State</span>
              <span className="text-slate-300">{ready?.redis?.toUpperCase() || 'CHECKING'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Operational Guidance Callout */}
      {isDegraded && (
        <div className="p-3.5 sm:p-4 rounded-xl bg-amber-950/20 border border-amber-500/40 text-amber-300 space-y-2">
          <div className="flex items-center gap-2 font-bold text-xs">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>Operational Troubleshooting Guidance</span>
          </div>
          <p className="text-[11px] font-sans text-amber-200/90 leading-relaxed break-words">
            The gateway is active but reported degraded readiness. Ensure the PostgreSQL connection pool is healthy on Supabase and verify Redis connectivity settings in the environment configuration.
          </p>
        </div>
      )}
    </div>
  );
};
