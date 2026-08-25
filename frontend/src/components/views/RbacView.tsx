import React from 'react';
import { Users, Shield, Lock, CheckCircle2, XCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { RoleEnum } from '../../types/api';
import { GlassCard } from '../layout/GlassCard';

export const RbacView: React.FC = () => {
  const { userRole, setUserRole } = useAuth();

  const roles: { role: RoleEnum; permissions: string[]; desc: string }[] = [
    { role: 'OWNER', permissions: ['Full Gateway Administration', 'Credential Creation/Revocation', 'Approval Authorization', 'Audit & SIEM Access'], desc: 'Complete tenant administration privileges.' },
    { role: 'ADMIN', permissions: ['Credential Management', 'Approval Authorization', 'Audit Explorer', 'SIEM Logs'], desc: 'Security operations administration.' },
    { role: 'APPROVER', permissions: ['HITL Ticket Approval & Rejection', 'Audit Logs Read-Only'], desc: 'Security officer approval authorization.' },
    { role: 'OPERATOR', permissions: ['Request Gateway Submission', 'Tool Execution', 'Audit Logs'], desc: 'Operational user requesting tool executions.' },
    { role: 'VIEWER', permissions: ['Audit Explorer Read-Only', 'Dashboard Metrics'], desc: 'Read-only audit & dashboard observer.' },
  ];

  return (
    <div className="space-y-6 font-mono text-xs">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          Role-Based Access Control (RBAC)
          <Users className="w-5 h-5 text-purple-400" />
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Server-side role hierarchy enforcing strict privilege boundaries
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {roles.map((r) => (
          <GlassCard key={r.role} glow={userRole === r.role ? 'cyan' : 'none'}>
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <strong className="text-purple-300 font-bold text-sm">{r.role}</strong>
                {userRole === r.role ? (
                  <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 text-[10px] border border-purple-500/40">
                    ACTIVE ROLE
                  </span>
                ) : (
                  <button
                    onClick={() => setUserRole(r.role)}
                    className="text-[10px] text-slate-400 hover:text-white underline"
                  >
                    Switch to Role
                  </button>
                )}
              </div>
              <p className="text-slate-400 text-[11px] font-sans">{r.desc}</p>
              <div className="space-y-1 pt-2 border-t border-slate-800/80">
                <span className="text-[10px] text-slate-500 block mb-1">Granted Privileges:</span>
                {r.permissions.map((p) => (
                  <div key={p} className="flex items-center gap-1.5 text-[11px] text-slate-300">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                    <span>{p}</span>
                  </div>
                ))}
              </div>
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  );
};
