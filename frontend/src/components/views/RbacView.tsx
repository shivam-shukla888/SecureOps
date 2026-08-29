import React, { useState } from 'react';
import {
  Users,
  Shield,
  ShieldCheck,
  ShieldAlert,
  Lock,
  CheckCircle2,
  XCircle,
  Search,
  Filter,
  RotateCcw,
  Info,
  UserCheck,
  Key,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { RoleEnum } from '../../types/api';

interface RoleDefinition {
  role: RoleEnum;
  level: number;
  label: string;
  desc: string;
  permissions: string[];
}

const ROLES_CATALOG: RoleDefinition[] = [
  {
    role: 'OWNER',
    level: 5,
    label: 'Tenant Owner',
    desc: 'Complete administrative authority over tenant resources, policies, and credentials.',
    permissions: [
      'Submit Gateway Requests',
      'Execute Governed Tools',
      'Inspect Audit Trail & SIEM Logs',
      'Authorize HITL Approvals',
      'Issue, Rotate & Revoke Credentials',
      'Full Tenant Governance',
    ],
  },
  {
    role: 'ADMIN',
    level: 4,
    label: 'Security Administrator',
    desc: 'Operational security management including credential lifecycle and approval escalation.',
    permissions: [
      'Submit Gateway Requests',
      'Execute Governed Tools',
      'Inspect Audit Trail & SIEM Logs',
      'Authorize HITL Approvals',
      'Issue, Rotate & Revoke Credentials',
    ],
  },
  {
    role: 'APPROVER',
    level: 3,
    label: 'Security Officer (Approver)',
    desc: 'Authorized to review, approve, and reject elevated-risk Human-in-the-Loop tickets.',
    permissions: [
      'Submit Gateway Requests',
      'Execute Governed Tools',
      'Inspect Audit Trail & SIEM Logs',
      'Authorize & Reject HITL Approvals',
    ],
  },
  {
    role: 'OPERATOR',
    level: 2,
    label: 'Agent / Operator',
    desc: 'Standard AI agent or service operator submitting requests and invoking permitted tools.',
    permissions: [
      'Submit Gateway Requests',
      'Execute Governed Tools (Policy Sandboxed)',
      'Inspect Scoped Audit Records',
    ],
  },
  {
    role: 'VIEWER',
    level: 1,
    label: 'Audit & Telemetry Viewer',
    desc: 'Read-only observer for security monitoring, compliance audits, and telemetry views.',
    permissions: [
      'Inspect Audit Trail & SIEM Telemetry',
      'View Dashboard Health & Metrics',
    ],
  },
];

interface TenantUser {
  user_id: string;
  name: string;
  role: RoleEnum;
  tenant_id: string;
  status: 'ACTIVE' | 'DISABLED';
  service_type: 'HUMAN' | 'AI_AGENT';
}

export const RbacView: React.FC = () => {
  const { userRole, setUserRole, tenantId, userId: currentUserId } = useAuth();

  const [roleFilter, setRoleFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedUser, setSelectedUser] = useState<TenantUser | null>(null);

  // Authoritative identity list for active tenant
  const tenantUsers: TenantUser[] = [
    {
      user_id: currentUserId || 'admin_user',
      name: 'Primary Security Administrator',
      role: 'ADMIN',
      tenant_id: tenantId,
      status: 'ACTIVE',
      service_type: 'HUMAN',
    },
    {
      user_id: 'security_officer_bob',
      name: 'Bob Vance (Security Officer)',
      role: 'APPROVER',
      tenant_id: tenantId,
      status: 'ACTIVE',
      service_type: 'HUMAN',
    },
    {
      user_id: 'operator_sarah',
      name: 'Sarah Connor (Agent Operator)',
      role: 'OPERATOR',
      tenant_id: tenantId,
      status: 'ACTIVE',
      service_type: 'HUMAN',
    },
    {
      user_id: 'agent_doc_searcher',
      name: 'Document Analysis Agent #01',
      role: 'OPERATOR',
      tenant_id: tenantId,
      status: 'ACTIVE',
      service_type: 'AI_AGENT',
    },
    {
      user_id: 'auditor_dave',
      name: 'Dave Bowman (Compliance Auditor)',
      role: 'VIEWER',
      tenant_id: tenantId,
      status: 'ACTIVE',
      service_type: 'HUMAN',
    },
  ];

  const filteredUsers = tenantUsers.filter((u) => {
    const matchesRole = roleFilter === 'ALL' || u.role === roleFilter;
    const query = searchTerm.toLowerCase().trim();
    const matchesSearch =
      !query ||
      u.user_id.toLowerCase().includes(query) ||
      u.name.toLowerCase().includes(query) ||
      u.role.toLowerCase().includes(query);
    return matchesRole && matchesSearch;
  });

  const handleResetFilters = () => {
    setRoleFilter('ALL');
    setSearchTerm('');
  };

  const getRoleBadgeStyle = (role: RoleEnum) => {
    switch (role) {
      case 'OWNER':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
      case 'ADMIN':
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
      case 'APPROVER':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'OPERATOR':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'VIEWER':
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="space-y-6 select-none font-mono text-xs">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-white tracking-tight uppercase">
              USERS & ROLES
            </h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-purple-500/10 text-purple-300 border border-purple-500/20">
              RBAC IAM
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Manage identities, roles, and authorization boundaries across SecureOps.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start md:self-auto">
          <div className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-[#111827] border border-slate-800 text-[11px] text-slate-400">
            <span>
              Tenant: <strong className="text-slate-200">{tenantId}</strong>
            </span>
            <span className="text-slate-700">|</span>
            <span>
              Active Role: <strong className="text-cyan-400">{userRole}</strong>
            </span>
          </div>
        </div>
      </div>

      {/* Role Hierarchy Cards */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-white uppercase flex items-center gap-2">
            <Shield className="w-4 h-4 text-purple-400" />
            <span>Role Hierarchy & Privilege Levels (5 Roles)</span>
          </h3>
          <span className="text-[10px] text-slate-500">
            Higher Level = Inherited Permissions
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {ROLES_CATALOG.map((r) => {
            const isCurrent = userRole === r.role;
            return (
              <div
                key={r.role}
                className={`p-4 rounded-xl border transition-all flex flex-col justify-between space-y-3 ${
                  isCurrent
                    ? 'bg-purple-950/20 border-purple-500/50 shadow-md'
                    : 'bg-[#111827] border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getRoleBadgeStyle(
                        r.role
                      )}`}
                    >
                      {r.role}
                    </span>
                    <span className="text-[10px] text-slate-500">L{r.level}</span>
                  </div>
                  <strong className="text-white text-xs block">{r.label}</strong>
                  <p className="text-slate-400 text-[11px] font-sans leading-snug">{r.desc}</p>
                </div>

                <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                  {isCurrent ? (
                    <span className="text-[10px] text-emerald-400 font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      ACTIVE ROLE
                    </span>
                  ) : (
                    <button
                      onClick={() => setUserRole(r.role)}
                      className="text-[10px] text-cyan-400 hover:text-cyan-300 underline cursor-pointer"
                    >
                      Switch to {r.role}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Permission Capability Matrix */}
      <div className="rounded-xl bg-[#111827] border border-slate-800/80 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-semibold text-white uppercase">
              Authoritative Permission Matrix
            </h3>
          </div>
          <span className="text-[10px] text-slate-500">Server-Enforced RBAC Rules</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-[11px]">
            <thead>
              <tr className="border-b border-slate-800 bg-[#0e1422] text-[10px] uppercase text-slate-400">
                <th className="p-3">Gateway Capability / Endpoint</th>
                <th className="p-3 text-center">VIEWER (L1)</th>
                <th className="p-3 text-center">OPERATOR (L2)</th>
                <th className="p-3 text-center">APPROVER (L3)</th>
                <th className="p-3 text-center">ADMIN (L4)</th>
                <th className="p-3 text-center">OWNER (L5)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              <tr>
                <td className="p-3 font-semibold text-slate-200">
                  Inspect Audit Trail & Security Events
                </td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
              </tr>
              <tr>
                <td className="p-3 font-semibold text-slate-200">
                  Submit AI Request to Gateway
                </td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
              </tr>
              <tr>
                <td className="p-3 font-semibold text-slate-200">
                  Execute Sandboxed Governed Tools
                </td>
                <td className="p-3 text-center text-slate-600">—</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
              </tr>
              <tr>
                <td className="p-3 font-semibold text-slate-200">
                  Authorize / Deny HITL Approval Tickets
                </td>
                <td className="p-3 text-center text-slate-600">—</td>
                <td className="p-3 text-center text-slate-600">—</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
              </tr>
              <tr>
                <td className="p-3 font-semibold text-slate-200">
                  Issue, Rotate & Revoke API Credentials
                </td>
                <td className="p-3 text-center text-slate-600">—</td>
                <td className="p-3 text-center text-slate-600">—</td>
                <td className="p-3 text-center text-slate-600">—</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
              </tr>
              <tr>
                <td className="p-3 font-semibold text-slate-200">
                  Tenant Governance & Security Configuration
                </td>
                <td className="p-3 text-center text-slate-600">—</td>
                <td className="p-3 text-center text-slate-600">—</td>
                <td className="p-3 text-center text-slate-600">—</td>
                <td className="p-3 text-center text-slate-600">—</td>
                <td className="p-3 text-center text-emerald-400">✓</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1 p-1 rounded-lg bg-[#111827] border border-slate-800 overflow-x-auto">
          {['ALL', 'OWNER', 'ADMIN', 'APPROVER', 'OPERATOR', 'VIEWER'].map((r) => (
            <button
              key={r}
              onClick={() => setRoleFilter(r)}
              className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer whitespace-nowrap ${
                roleFilter === r
                  ? 'bg-slate-800 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search user, name, role..."
              className="w-full bg-[#111827] border border-slate-800 focus:border-cyan-500 rounded-lg py-1.5 pl-8 pr-3 text-slate-200 focus:outline-none placeholder:text-slate-600"
            />
          </div>

          {(roleFilter !== 'ALL' || searchTerm) && (
            <button
              onClick={handleResetFilters}
              className="px-2.5 py-1.5 rounded-lg bg-[#111827] border border-slate-800 text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors cursor-pointer"
              title="Reset active filters"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Grid: User Table (7 cols) + Detail Inspector (5 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: User Identities */}
        <div className="lg:col-span-7 space-y-4">
          <div className="rounded-xl bg-[#111827] border border-slate-800/80 overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <span className="text-slate-400 font-medium">
                {filteredUsers.length} Active {filteredUsers.length === 1 ? 'Identity' : 'Identities'}
              </span>
              <span className="text-[10px] text-cyan-400 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                Tenant Scoped
              </span>
            </div>

            {filteredUsers.length === 0 ? (
              <div className="p-12 text-center text-slate-500 space-y-2">
                <Users className="w-8 h-8 mx-auto text-slate-600" />
                <p className="text-slate-300 font-medium">No users found</p>
                <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
                  Users and agent service principals associated with this tenant will appear here.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-[#0e1422] text-[10px] uppercase text-slate-400">
                      <th className="p-3">Identity / User ID</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Assigned Role</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Inspect</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredUsers.map((u) => {
                      const isSelected = selectedUser?.user_id === u.user_id;
                      return (
                        <tr
                          key={u.user_id}
                          onClick={() => setSelectedUser(u)}
                          className={`hover:bg-[#151c2e] cursor-pointer transition-colors ${
                            isSelected ? 'bg-[#18233a]' : ''
                          }`}
                        >
                          <td className="p-3">
                            <span className="text-slate-200 font-bold block">{u.name}</span>
                            <span className="text-[10px] text-cyan-400 select-all block">
                              {u.user_id}
                            </span>
                          </td>
                          <td className="p-3">
                            <span className="text-[10px] text-slate-400 px-1.5 py-0.5 rounded bg-slate-800/60 border border-slate-700">
                              {u.service_type}
                            </span>
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getRoleBadgeStyle(
                                u.role
                              )}`}
                            >
                              {u.role}
                            </span>
                          </td>
                          <td className="p-3">
                            <span className="text-emerald-400 text-[10px] font-bold">
                              {u.status}
                            </span>
                          </td>
                          <td className="p-3 text-right">
                            <ArrowRight className="w-3.5 h-3.5 inline text-slate-500" />
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

        {/* Right Column: User Detail Inspector */}
        <div className="lg:col-span-5 space-y-4">
          {selectedUser ? (
            <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4">
              <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-white text-sm uppercase">Identity Context</h3>
                  <span className="text-[10px] text-cyan-400 select-all">
                    {selectedUser.user_id}
                  </span>
                </div>
                <span
                  className={`px-2.5 py-0.5 rounded text-[10px] font-bold border ${getRoleBadgeStyle(
                    selectedUser.role
                  )}`}
                >
                  {selectedUser.role}
                </span>
              </div>

              {/* User Identity Details */}
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Principal Information
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Display Name:</span>
                    <strong className="text-slate-200">{selectedUser.name}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">User ID:</span>
                    <strong className="text-slate-200 select-all">{selectedUser.user_id}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Tenant:</span>
                    <strong className="text-slate-200">{selectedUser.tenant_id}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Principal Type:</span>
                    <span className="text-cyan-300">{selectedUser.service_type}</span>
                  </div>
                </div>
              </div>

              {/* Separation of Duties Notice */}
              <div className="p-3.5 rounded-lg bg-[#0e1422] border border-slate-800 text-slate-400 text-xs flex items-start gap-2.5">
                <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <div className="text-[11px] leading-relaxed">
                  <strong className="text-slate-200 block mb-0.5">
                    Separation of Duties
                  </strong>
                  To prevent privilege abuse, the approver and requester of an elevated operation must be distinct security principals.
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-xl bg-[#111827] border border-slate-800/80 text-center space-y-3">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 mx-auto">
                <Users className="w-5 h-5" />
              </div>
              <h4 className="text-xs font-semibold text-white uppercase">
                No Identity Selected
              </h4>
              <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
                Select a user or AI agent principal from the list on the left to inspect detailed role permissions and tenant boundary bindings.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
