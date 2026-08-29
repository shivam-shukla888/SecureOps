import React, { useState } from 'react';
import {
  Building2,
  Shield,
  ShieldCheck,
  ShieldAlert,
  Lock,
  Users,
  Search,
  RotateCcw,
  CheckCircle2,
  Layers,
  ArrowRight,
  Info,
  Server,
  Database,
  Cpu,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export interface TenantWorkspace {
  id: string;
  name: string;
  status: 'ACTIVE' | 'SUSPENDED';
  tier: 'ENTERPRISE' | 'GOVERNMENT' | 'STANDARD';
  description: string;
  isolation_controls: string[];
}

export const TENANTS_CATALOG: TenantWorkspace[] = [
  {
    id: 'tenant_default',
    name: 'Primary Enterprise Gateway Workspace',
    status: 'ACTIVE',
    tier: 'ENTERPRISE',
    description: 'Production tenant workspace isolating security events, approvals, credentials, and governed executions.',
    isolation_controls: [
      'Row-Level PostgreSQL Tenant Keying',
      'Redis Sliding Window Rate Limit Partitioning (tenant:user)',
      'Time-Bound HITL Approval Queue Isolation',
      'Cryptographically Committed Audit Log Partitioning',
    ],
  },
  {
    id: 'tenant_acme',
    name: 'Acme Corporation Security Workspace',
    status: 'ACTIVE',
    tier: 'ENTERPRISE',
    description: 'Dedicated enterprise workspace for Acme Corp AI-agent integrations and sandbox tools.',
    isolation_controls: [
      'Multi-Tenant Cryptographic Partitioning',
      'Tenant-Scoped Role Hierarchy',
      'Isolated Document Index Adapters',
      'Independent Rate Limit Windows',
    ],
  },
  {
    id: 'tenant_globex',
    name: 'Globex International Operations',
    status: 'ACTIVE',
    tier: 'GOVERNMENT',
    description: 'High-assurance operational workspace with dedicated audit trails and strict approval thresholds.',
    isolation_controls: [
      'High-Assurance Tenant Scoping',
      'Strict Separation of Duties Enforcement',
      'SSRF Destination Whitelisting Isolation',
      'Dedicated SHA-256 Audit Stream',
    ],
  },
];

export const TenantsView: React.FC = () => {
  const { tenantId, setTenantId, userRole } = useAuth();

  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedTenant, setSelectedTenant] = useState<TenantWorkspace | null>(
    TENANTS_CATALOG.find((t) => t.id === tenantId) || TENANTS_CATALOG[0]
  );

  const filteredTenants = TENANTS_CATALOG.filter((t) => {
    if (!searchTerm.trim()) return true;
    const query = searchTerm.toLowerCase().trim();
    return (
      t.id.toLowerCase().includes(query) ||
      t.name.toLowerCase().includes(query) ||
      t.tier.toLowerCase().includes(query) ||
      t.description.toLowerCase().includes(query)
    );
  });

  const handleSelectActive = (id: string) => {
    setTenantId(id);
    const found = TENANTS_CATALOG.find((t) => t.id === id);
    if (found) setSelectedTenant(found);
  };

  return (
    <div className="space-y-6 select-none font-mono text-xs">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-white tracking-tight uppercase">
              TENANT MANAGEMENT
            </h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              MULTI-TENANCY ISOLATION
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Manage multi-tenant workspace partitioning and strict security isolation boundaries.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start md:self-auto">
          <div className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-[#111827] border border-slate-800 text-[11px] text-slate-400">
            <span>
              Active Tenant: <strong className="text-cyan-400 select-all">{tenantId}</strong>
            </span>
            <span className="text-slate-700">|</span>
            <span>
              Role: <strong className="text-slate-200">{userRole}</strong>
            </span>
          </div>
        </div>
      </div>

      {/* Architectural Isolation Banner */}
      <div className="p-4 rounded-xl bg-[#0e1422] border border-slate-800/80 text-slate-400 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
        <div className="text-[11px] leading-relaxed">
          <strong className="text-slate-200 block mb-0.5">
            Cryptographic & Logical Tenant Partitioning
          </strong>
          Security boundaries in SecureOps are strictly tenant-scoped. Audit logs, approval tickets, rate limits, and API credentials are isolated to prevent cross-tenant information leakage.
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center justify-between gap-3">
        <div className="relative flex-1 sm:w-72">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search tenant ID, name, tier..."
            className="w-full bg-[#111827] border border-slate-800 focus:border-cyan-500 rounded-lg py-1.5 pl-8 pr-3 text-xs text-slate-200 focus:outline-none placeholder:text-slate-600"
          />
        </div>

        {searchTerm && (
          <button
            onClick={() => setSearchTerm('')}
            className="px-2.5 py-1.5 rounded-lg bg-[#111827] border border-slate-800 text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors cursor-pointer"
            title="Reset active search"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Reset</span>
          </button>
        )}
      </div>

      {/* Main Grid: Tenant Inventory (7 cols) + Detail Inspector (5 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Tenant Inventory */}
        <div className="lg:col-span-7 space-y-4">
          <div className="rounded-xl bg-[#111827] border border-slate-800/80 overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <span className="text-slate-400 font-medium">
                {filteredTenants.length} Partitioned{' '}
                {filteredTenants.length === 1 ? 'Workspace' : 'Workspaces'}
              </span>
              <span className="text-[10px] text-cyan-400 flex items-center gap-1">
                <Database className="w-3.5 h-3.5" />
                Row-Level Scoped
              </span>
            </div>

            {filteredTenants.length === 0 ? (
              <div className="p-12 text-center text-slate-500 space-y-2">
                <Building2 className="w-8 h-8 mx-auto text-slate-600" />
                <p className="text-slate-300 font-medium">No tenants found</p>
                <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
                  Adjust your search filter to inspect registered tenant partitions.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-[#0e1422] text-[10px] uppercase text-slate-400">
                      <th className="p-3">Tenant Workspace</th>
                      <th className="p-3">Tier</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Workspace Scope</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredTenants.map((t) => {
                      const isActive = tenantId === t.id;
                      const isSelected = selectedTenant?.id === t.id;
                      return (
                        <tr
                          key={t.id}
                          onClick={() => setSelectedTenant(t)}
                          className={`hover:bg-[#151c2e] cursor-pointer transition-colors ${
                            isSelected ? 'bg-[#18233a]' : ''
                          }`}
                        >
                          <td className="p-3">
                            <div className="flex items-center gap-2">
                              <span className="text-slate-200 font-bold block">{t.name}</span>
                              {isActive && (
                                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                                  ACTIVE
                                </span>
                              )}
                            </div>
                            <span className="text-[10px] text-cyan-400 select-all block mt-0.5">
                              {t.id}
                            </span>
                          </td>
                          <td className="p-3">
                            <span className="text-[10px] text-purple-300 px-1.5 py-0.5 rounded bg-purple-500/10 border border-purple-500/20">
                              {t.tier}
                            </span>
                          </td>
                          <td className="p-3">
                            <span className="text-emerald-400 text-[10px] font-bold">
                              {t.status}
                            </span>
                          </td>
                          <td className="p-3 text-right">
                            {isActive ? (
                              <span className="text-[10px] text-cyan-400 font-bold">
                                Current
                              </span>
                            ) : (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleSelectActive(t.id);
                                }}
                                className="text-[10px] text-slate-400 hover:text-white underline"
                              >
                                Switch
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Tenant Detail Inspector */}
        <div className="lg:col-span-5 space-y-4">
          {selectedTenant ? (
            <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4">
              <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-white text-sm uppercase">Tenant Workspace</h3>
                  <span className="text-[10px] text-cyan-400 select-all">
                    {selectedTenant.id}
                  </span>
                </div>
                <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  {selectedTenant.status}
                </span>
              </div>

              {/* Tenant Identity Details */}
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Identity & Tier
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Workspace Label:</span>
                    <strong className="text-slate-200">{selectedTenant.name}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Tenant Identifier:</span>
                    <strong className="text-cyan-400 select-all">{selectedTenant.id}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Assurance Tier:</span>
                    <strong className="text-purple-300">{selectedTenant.tier}</strong>
                  </div>
                  <div className="pt-1 border-t border-slate-800 text-[11px] text-slate-300">
                    {selectedTenant.description}
                  </div>
                </div>
              </div>

              {/* Data Isolation Controls */}
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Active Isolation Controls
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-1.5">
                  {selectedTenant.isolation_controls.map((ctrl, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-[11px] text-slate-300">
                      <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                      <span>{ctrl}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Workspace Action */}
              <div className="pt-2 border-t border-slate-800 flex justify-end">
                {tenantId === selectedTenant.id ? (
                  <span className="text-[11px] text-emerald-400 font-bold flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    Active Workspace
                  </span>
                ) : (
                  <button
                    onClick={() => handleSelectActive(selectedTenant.id)}
                    className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs flex items-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <Building2 className="w-3.5 h-3.5" />
                    <span>Set as Active Workspace</span>
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-xl bg-[#111827] border border-slate-800/80 text-center space-y-3">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mx-auto">
                <Building2 className="w-5 h-5" />
              </div>
              <h4 className="text-xs font-semibold text-white uppercase">
                No Workspace Selected
              </h4>
              <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
                Select a tenant workspace from the table on the left to inspect multi-tenancy isolation controls and security boundary policies.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
