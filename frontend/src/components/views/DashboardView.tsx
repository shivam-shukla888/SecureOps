import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  Zap,
  Activity,
  Cpu,
  Database,
  Layers,
  Sparkles,
  ArrowUpRight,
  TrendingUp,
} from 'lucide-react';
import { api } from '../../services/api';
import { GlassCard } from '../layout/GlassCard';

export const DashboardView: React.FC = () => {
  const { data: summary, isLoading: summaryLoading, isError: summaryError, refetch } = useQuery({
    queryKey: ['dashboardSummary'],
    queryFn: () => api.getDashboardSummary(),
    refetchInterval: 10000,
  });

  const { data: readiness } = useQuery({
    queryKey: ['systemReadiness'],
    queryFn: () => api.getReady(),
    refetchInterval: 15000,
  });

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            Security Command Center
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Real-Time AI Request Telemetry & Security Operations Control
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="px-3 py-1.5 rounded-lg bg-[#161e31] border border-slate-800 hover:border-cyan-500/40 text-xs font-mono text-cyan-400 flex items-center gap-1.5 transition-colors"
        >
          <Activity className="w-3.5 h-3.5" />
          Refresh Live Metrics
        </button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Requests */}
        <GlassCard glow="cyan">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono text-slate-400">Total Requests Today</span>
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {summaryLoading ? '...' : summary?.requests_today ?? 0}
          </div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center gap-1">
            <TrendingUp className="w-3 h-3 text-cyan-400" />
            <span>Monitored via Gateway</span>
          </div>
        </GlassCard>

        {/* Allowed Requests */}
        <GlassCard glow="emerald">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono text-slate-400">Allowed Requests</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">
            {summaryLoading ? '...' : summary?.allowed_requests ?? 0}
          </div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            <span>Passed Security Policy</span>
          </div>
        </GlassCard>

        {/* Blocked Requests */}
        <GlassCard glow="rose">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono text-slate-400">Blocked Requests</span>
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400">
              <XCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-rose-400 font-mono">
            {summaryLoading ? '...' : summary?.blocked_requests ?? 0}
          </div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center gap-1">
            <ShieldAlert className="w-3 h-3 text-rose-400" />
            <span>Policy Engine Enforced</span>
          </div>
        </GlassCard>

        {/* Pending Approvals */}
        <GlassCard glow="none">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono text-slate-400">Pending Approvals</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-amber-400 font-mono">
            {summaryLoading ? '...' : summary?.pending_approvals ?? 0}
          </div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center gap-1">
            <Layers className="w-3 h-3 text-amber-400" />
            <span>Awaiting Security Officer</span>
          </div>
        </GlassCard>
      </div>

      {/* Provider Status & Infrastructure Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Provider Status */}
        <GlassCard>
          <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-semibold text-white">AI Provider Fallback Chain</h2>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Fallbacks Used: <strong className="text-amber-400">{summary?.provider_fallbacks ?? 0}</strong>
            </span>
          </div>

          <div className="space-y-3">
            {/* Primary Provider: Gemini */}
            <div className="p-3.5 rounded-xl bg-[#0d1322] border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center font-bold text-xs text-cyan-400">
                  G
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-slate-200">Gemini 2.5 Flash</h3>
                  <p className="text-[10px] text-slate-400 font-mono">Primary Classifier</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono">
                  ONLINE
                </span>
              </div>
            </div>

            {/* Fallback Provider: Groq */}
            <div className="p-3.5 rounded-xl bg-[#0d1322] border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center font-bold text-xs text-amber-400">
                  Q
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-slate-200">Groq Llama-3.3-70b</h3>
                  <p className="text-[10px] text-slate-400 font-mono">Automatic Fallback</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono">
                  STANDBY
                </span>
              </div>
            </div>
          </div>
        </GlassCard>

        {/* System Infrastructure Status */}
        <GlassCard>
          <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-semibold text-white">Infrastructure Status</h2>
            </div>
            <span className="text-[11px] font-mono text-emerald-400">
              {readiness?.status === 'ready' ? 'SYSTEM READY' : 'DEGRADED'}
            </span>
          </div>

          <div className="space-y-3">
            {/* Rate Limiter */}
            <div className="p-3.5 rounded-xl bg-[#0d1322] border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Activity className="w-5 h-5 text-cyan-400" />
                <div>
                  <h3 className="text-xs font-semibold text-slate-200">Sliding Window Rate Limiter</h3>
                  <p className="text-[10px] text-slate-400 font-mono">Backend: In-Memory / Redis</p>
                </div>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono">
                {readiness?.rate_limiter?.toUpperCase() || 'READY'}
              </span>
            </div>

            {/* Database Persistence */}
            <div className="p-3.5 rounded-xl bg-[#0d1322] border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Database className="w-5 h-5 text-emerald-400" />
                <div>
                  <h3 className="text-xs font-semibold text-slate-200">PostgreSQL Data Store</h3>
                  <p className="text-[10px] text-slate-400 font-mono">Audit & Ticket Partitioning</p>
                </div>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono">
                {readiness?.database?.toUpperCase() || 'READY'}
              </span>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};
