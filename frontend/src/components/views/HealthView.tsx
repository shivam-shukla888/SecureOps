import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, CheckCircle2, Cpu, Database, Layers, ShieldCheck, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { GlassCard } from '../layout/GlassCard';

export const HealthView: React.FC = () => {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['healthCheck'],
    queryFn: () => api.getHealth(),
    refetchInterval: 10000,
  });

  const { data: ready, isLoading: readyLoading, refetch } = useQuery({
    queryKey: ['readinessCheck'],
    queryFn: () => api.getReady(),
    refetchInterval: 10000,
  });

  return (
    <div className="space-y-6 font-mono text-xs">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            System Health & Readiness Monitor
            <Activity className="w-5 h-5 text-emerald-400" />
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Real-time liveness (/health) and readiness (/ready) telemetry
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="px-3 py-1.5 rounded-lg bg-[#161e31] border border-slate-800 text-cyan-400 flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Re-Check Telemetry
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Liveness */}
        <GlassCard glow="emerald">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h2 className="font-bold text-white text-sm">Application Liveness (/health)</h2>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">
                {health?.status?.toUpperCase() || 'LOADING'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Service Name</span>
              <strong className="text-slate-200">{health?.service || 'SecureOps API Gateway'}</strong>
            </div>
            <div>
              <span className="text-slate-500 block">Timestamp</span>
              <strong className="text-slate-400 text-[11px]">{health?.timestamp}</strong>
            </div>
          </div>
        </GlassCard>

        {/* Readiness */}
        <GlassCard glow="cyan">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h2 className="font-bold text-white text-sm">System Readiness (/ready)</h2>
              <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-400 font-bold">
                {ready?.status?.toUpperCase() || 'LOADING'}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-1">
              <div className="p-2.5 rounded bg-[#0a0f1b] border border-slate-800">
                <span className="text-slate-500 text-[10px] block">Rate Limiter</span>
                <strong className="text-emerald-400">{ready?.rate_limiter?.toUpperCase()}</strong>
              </div>
              <div className="p-2.5 rounded bg-[#0a0f1b] border border-slate-800">
                <span className="text-slate-500 text-[10px] block">Database</span>
                <strong className="text-emerald-400">{ready?.database?.toUpperCase()}</strong>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};
