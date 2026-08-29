import React from 'react';
import {
  Settings as SettingsIcon,
  ShieldCheck,
  ShieldAlert,
  Lock,
  Globe,
  Database,
  Cpu,
  Layers,
  Info,
  Key,
  UserCheck,
  CheckCircle2,
  Sliders,
  Server,
  Zap,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const SettingsView: React.FC = () => {
  const { tenantId, userRole, userId } = useAuth();

  return (
    <div className="space-y-6 select-none font-mono text-xs">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-white tracking-tight uppercase">
              SETTINGS & SECURITY CONTROLS
            </h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              ENVIRONMENT GOVERNANCE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Manage available SecureOps configuration and account context.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start md:self-auto">
          <div className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-[#111827] border border-slate-800 text-[11px] text-slate-400">
            <span>
              Tenant: <strong className="text-slate-200">{tenantId}</strong>
            </span>
            <span className="text-slate-700">|</span>
            <span>
              Role: <strong className="text-cyan-400">{userRole}</strong>
            </span>
          </div>
        </div>
      </div>

      {/* Read-Only Governance Banner */}
      <div className="p-4 rounded-xl bg-[#0e1422] border border-slate-800/80 text-slate-400 flex items-start gap-3">
        <Lock className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
        <div className="text-[11px] leading-relaxed">
          <div className="flex items-center gap-2 mb-0.5">
            <strong className="text-slate-200">
              Immutable Server-Side Security Policy
            </strong>
            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-slate-800 text-slate-400 border border-slate-700">
              READ ONLY
            </span>
          </div>
          Gateway execution parameters, SSRF egress allowlists, and rate limits are defined by infrastructure environment configuration and enforced deterministically on the server.
        </div>
      </div>

      {/* Main Settings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Section 1: Account & Session Context */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-purple-400" />
              <h2 className="text-xs font-semibold text-white uppercase">
                Account & Session Context
              </h2>
            </div>
            <span className="text-[10px] text-slate-500 uppercase">AuthContext</span>
          </div>

          <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-2.5">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Authenticated Principal:</span>
              <strong className="text-slate-200 select-all">{userId || 'admin_operator'}</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Assigned RBAC Role:</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                {userRole}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Active Tenant Partition:</span>
              <strong className="text-cyan-400 select-all">{tenantId}</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Session Vault Mode:</span>
              <span className="text-emerald-400 font-bold">SHA-256 Hashed Key</span>
            </div>
          </div>
        </div>

        {/* Section 2: SSRF Outbound Egress Policy */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-emerald-400" />
              <h2 className="text-xs font-semibold text-white uppercase">
                SSRF Outbound Egress Policy
              </h2>
            </div>
            <span className="text-[10px] text-emerald-400 font-bold">ENFORCED</span>
          </div>

          <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-2.5">
            <div className="space-y-1">
              <span className="text-slate-400 block text-[10px]">
                BLOCKED PRIVATE & CLOUD METADATA RANGES
              </span>
              <div className="p-2 rounded bg-[#0a0f1b] border border-rose-500/30 text-rose-300 text-[11px] font-mono select-all">
                127.0.0.1, 169.254.169.254, 10.0.0.0/8, 192.168.0.0/16
              </div>
            </div>
            <div className="space-y-1 pt-1">
              <span className="text-slate-400 block text-[10px]">
                ALLOWLISTED DESTINATION HOSTS
              </span>
              <div className="p-2 rounded bg-[#0a0f1b] border border-emerald-500/30 text-emerald-300 text-[11px] font-mono select-all">
                api.internal-doc-service.com, alphhha.app.n8n.cloud
              </div>
            </div>
          </div>
        </div>

        {/* Section 3: Gateway Execution Parameters */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <h2 className="text-xs font-semibold text-white uppercase">
                Gateway Execution Parameters
              </h2>
            </div>
            <span className="text-[10px] text-slate-500">Limits</span>
          </div>

          <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-2.5">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Tool Execution Timeout:</span>
              <strong className="text-slate-200">10.0 seconds</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">HITL Ticket Expiry:</span>
              <strong className="text-slate-200">60 minutes (Time-Bound)</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Max Request Payload Size:</span>
              <strong className="text-slate-200">1,048,576 bytes (1 MB)</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Max Request Prompt Length:</span>
              <strong className="text-slate-200">4,000 characters</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Idempotency Key TTL:</span>
              <strong className="text-slate-200">86,400 seconds (24h)</strong>
            </div>
          </div>
        </div>

        {/* Section 4: AI Classification & Fallback Cascade */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              <h2 className="text-xs font-semibold text-white uppercase">
                AI Classification Cascade
              </h2>
            </div>
            <span className="text-[10px] text-amber-400 font-bold">3 TIERS</span>
          </div>

          <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-2.5">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Primary Classifier:</span>
              <strong className="text-cyan-300">gpt-4o-mini</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Fallback Tier 1:</span>
              <strong className="text-purple-300">gemini-3.5-flash</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Fallback Tier 2:</span>
              <strong className="text-amber-300">openai/gpt-oss-20b</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Deterministic Safety Fallback:</span>
              <span className="text-emerald-400 font-bold">Regex Pattern Engine</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
