import React from 'react';
import { Building2, Shield, Lock, Users } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { GlassCard } from '../layout/GlassCard';

export const TenantsView: React.FC = () => {
  const { tenantId, setTenantId } = useAuth();

  const tenants = [
    { id: 'tenant_default', name: 'Default Enterprise Tenant', users: 12, status: 'Active' },
    { id: 'tenant_acme', name: 'Acme Corporation Workspace', users: 8, status: 'Active' },
    { id: 'tenant_globex', name: 'Globex International Workspace', users: 5, status: 'Active' },
  ];

  return (
    <div className="space-y-6 font-mono text-xs">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          Multi-Tenancy Workspace Manager
          <Building2 className="w-5 h-5 text-cyan-400" />
        </h1>
        <p className="text-xs text-slate-400 mt-0.5 font-mono">
          Strict data partitioning isolating logs, tickets, and execution state by tenant ID
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {tenants.map((t) => (
          <GlassCard
            key={t.id}
            glow={tenantId === t.id ? 'cyan' : 'none'}
            onClick={() => setTenantId(t.id)}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <strong className="text-white font-bold">{t.name}</strong>
                {tenantId === t.id && (
                  <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-400 text-[10px]">SELECTED</span>
                )}
              </div>
              <p className="text-slate-400 text-[11px]">Tenant Identifier: <code className="text-cyan-300">{t.id}</code></p>
              <div className="flex justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-800/80">
                <span>Active Users: {t.users}</span>
                <span className="text-emerald-400">{t.status}</span>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  );
};
