import React from 'react';
import { Settings as SettingsIcon, ShieldCheck, Lock, Globe, Database } from 'lucide-react';
import { GlassCard } from '../layout/GlassCard';

export const SettingsView: React.FC = () => {
  return (
    <div className="space-y-6 font-mono text-xs">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          Security Controls & Gateway Settings
          <SettingsIcon className="w-5 h-5 text-cyan-400" />
        </h1>
        <p className="text-xs text-slate-400 mt-0.5 font-mono">
          Global security configuration, SSRF egress allowlists, and execution parameters
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <GlassCard>
          <div className="space-y-3">
            <h2 className="font-bold text-white text-sm border-b border-slate-800 pb-2">
              SSRF Outbound Egress Policy
            </h2>
            <div className="p-3 rounded-lg bg-[#0a0f1b] border border-slate-800 space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Blocked Targets:</span>
                <strong className="text-rose-400">127.0.0.1, 169.254.169.254, 10.0.0.0/8</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Allowlisted Webhooks:</span>
                <strong className="text-emerald-400">https://alphhha.app.n8n.cloud</strong>
              </div>
            </div>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="space-y-3">
            <h2 className="font-bold text-white text-sm border-b border-slate-800 pb-2">
              Gateway Execution Parameters
            </h2>
            <div className="p-3 rounded-lg bg-[#0a0f1b] border border-slate-800 space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Execution Timeout:</span>
                <strong className="text-slate-200">10.0 seconds</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Approval Expiry:</span>
                <strong className="text-slate-200">60 minutes</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Max Request Size:</span>
                <strong className="text-slate-200">1,048,576 bytes</strong>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};
