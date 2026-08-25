import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldCheck,
  LayoutDashboard,
  Send,
  CheckSquare,
  FileText,
  AlertTriangle,
  Play,
  Wrench,
  Building2,
  Users,
  Key,
  Activity,
  Settings as SettingsIcon,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarItem {
  path: string;
  label: string;
  icon: React.ElementType;
  badge?: number;
}

export const Sidebar: React.FC = () => {
  const { logout, userRole } = useAuth();

  const navItems: SidebarItem[] = [
    { path: '/dashboard', label: 'Command Center', icon: LayoutDashboard },
    { path: '/gateway', label: 'Request Gateway', icon: Send },
    { path: '/approvals', label: 'Approval Center', icon: CheckSquare },
    { path: '/security-events', label: 'Security Events', icon: AlertTriangle },
    { path: '/audit', label: 'Audit Explorer', icon: FileText },
    { path: '/executions', label: 'Execution Center', icon: Play },
    { path: '/tools', label: 'Tools & Permissions', icon: Wrench },
    { path: '/tenants', label: 'Tenants', icon: Building2 },
    { path: '/rbac', label: 'RBAC / Users', icon: Users },
    { path: '/credentials', label: 'Credentials', icon: Key },
    { path: '/health', label: 'System Health', icon: Activity },
    { path: '/settings', label: 'Security Settings', icon: SettingsIcon },
  ];

  return (
    <aside className="w-64 bg-[#0d1322] border-r border-slate-800/80 flex flex-col h-screen sticky top-0 z-30 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/80 flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-cyan-600 to-emerald-500 flex items-center justify-center shadow-glow-cyan">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-lg text-white tracking-wide flex items-center gap-1.5">
            SecureOps
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-400 font-mono border border-cyan-500/30">
              v5.0
            </span>
          </h1>
          <p className="text-[11px] text-slate-400 font-mono">Enterprise AI Gateway</p>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-1 custom-scrollbar">
        <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-500 uppercase tracking-wider font-mono">
          Security Controls
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 font-semibold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Profile & Logout */}
      <div className="p-4 border-t border-slate-800/80 bg-[#0a0f1b]/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-cyan-400 font-mono shrink-0">
              {userRole[0]}
            </div>
            <div className="truncate">
              <p className="text-xs font-medium text-slate-200 truncate">SecOps User</p>
              <span className="text-[10px] text-cyan-400 font-mono uppercase bg-cyan-950/50 px-1.5 py-0.5 rounded border border-cyan-800/50">
                {userRole}
              </span>
            </div>
          </div>
          <button
            onClick={logout}
            title="Disconnect / Logout"
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
