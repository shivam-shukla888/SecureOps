import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  Shield,
  LayoutDashboard,
  Send,
  Play,
  Wrench,
  ShieldAlert,
  FileText,
  CheckSquare,
  KeyRound,
  Users,
  Building2,
  Activity,
  Settings as SettingsIcon,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  X,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface NavItem {
  path: string;
  label: string;
  icon: React.ElementType;
  badge?: string | number;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

interface SidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  mobileOpen = false,
  onCloseMobile,
}) => {
  const { logout, userRole } = useAuth();
  const [collapsed, setCollapsed] = useState<boolean>(false);

  // Close mobile drawer on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && mobileOpen && onCloseMobile) {
        onCloseMobile();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mobileOpen, onCloseMobile]);

  // Lock body scroll when mobile drawer is open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileOpen]);

  const navigationGroups: NavGroup[] = [
    {
      title: 'COMMAND CENTER',
      items: [
        { path: '/dashboard', label: 'Overview', icon: LayoutDashboard },
        { path: '/gateway', label: 'Request Gateway', icon: Send },
        { path: '/executions', label: 'Executions', icon: Play },
        { path: '/tools', label: 'Tool Governance', icon: Wrench },
      ],
    },
    {
      title: 'SECURITY',
      items: [
        { path: '/security-events', label: 'Security Events', icon: ShieldAlert },
        { path: '/audit', label: 'Audit Explorer', icon: FileText },
        { path: '/approvals', label: 'Approval Center', icon: CheckSquare },
      ],
    },
    {
      title: 'ACCESS',
      items: [
        { path: '/credentials', label: 'Credentials', icon: KeyRound },
        { path: '/rbac', label: 'Users & Roles', icon: Users },
        { path: '/tenants', label: 'Tenants', icon: Building2 },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { path: '/health', label: 'System Health', icon: Activity },
        { path: '/settings', label: 'Settings', icon: SettingsIcon },
      ],
    },
  ];

  const renderNavLinks = (isMobile: boolean = false) => (
    <nav className="flex-1 overflow-y-auto px-2.5 py-3 space-y-4 custom-scrollbar">
      {navigationGroups.map((group) => (
        <div key={group.title} className="space-y-1">
          {!collapsed || isMobile ? (
            <div className="px-3 py-1 text-[10px] font-semibold text-slate-500 font-mono tracking-wider">
              {group.title}
            </div>
          ) : (
            <div className="h-px bg-slate-800/60 my-2 mx-2" />
          )}

          <ul className="space-y-1">
            {group.items.map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    onClick={() => {
                      if (isMobile && onCloseMobile) {
                        onCloseMobile();
                      }
                    }}
                    title={collapsed && !isMobile ? item.label : undefined}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 sm:py-2 min-h-[44px] sm:min-h-0 rounded-lg text-xs font-medium transition-colors ${
                        collapsed && !isMobile ? 'justify-center px-2' : ''
                      } ${
                        isActive
                          ? 'bg-slate-800/90 text-cyan-300 font-semibold border border-slate-700/70 shadow-sm'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 shrink-0 text-slate-400 group-hover:text-slate-200" />
                    {(!collapsed || isMobile) && (
                      <span className="truncate">{item.label}</span>
                    )}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );

  return (
    <>
      {/* MOBILE DRAWER BACKDROP */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/75 backdrop-blur-sm z-40 lg:hidden transition-opacity duration-200"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      {/* MOBILE SLIDE-OVER DRAWER (< lg) */}
      <aside
        id="mobile-navigation-drawer"
        aria-label="Mobile Navigation Menu"
        aria-modal={mobileOpen}
        role="dialog"
        className={`fixed inset-y-0 left-0 w-72 max-w-[85vw] bg-[#0b101b] border-r border-slate-800/80 z-50 flex flex-col h-dvh lg:hidden shadow-2xl transition-transform duration-200 ease-in-out select-none ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Mobile Drawer Header */}
        <div className="h-16 px-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
              <Shield className="w-4 h-4" />
            </div>
            <div className="truncate">
              <h2 className="font-bold text-xs tracking-wider text-slate-100 uppercase font-mono leading-none">
                SECUREOPS
              </h2>
              <p className="text-[9px] text-slate-400 font-mono tracking-wider mt-1">
                AI SECURITY GATEWAY
              </p>
            </div>
          </div>

          <button
            onClick={onCloseMobile}
            className="p-2 min-h-[44px] min-w-[44px] rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-colors flex items-center justify-center cursor-pointer"
            aria-label="Close navigation menu"
            title="Close navigation menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Mobile Navigation List */}
        {renderNavLinks(true)}

        {/* Mobile Footer Profile & Logout */}
        <div className="p-3.5 border-t border-slate-800/80 bg-[#090d16]/90">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-cyan-400 font-mono shrink-0">
                {userRole ? userRole[0] : 'U'}
              </div>
              <div className="truncate">
                <p className="text-xs font-medium text-slate-200 truncate">SecOps Admin</p>
                <div className="flex items-center gap-1 mt-0.5">
                  <span className="text-[9px] text-cyan-400 font-mono uppercase bg-cyan-950/60 px-1 py-0.2 rounded border border-cyan-800/50 leading-tight">
                    {userRole}
                  </span>
                </div>
              </div>
            </div>
            <button
              onClick={() => {
                if (onCloseMobile) onCloseMobile();
                logout();
              }}
              title="Disconnect / Logout"
              className="p-2 min-h-[44px] min-w-[44px] text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 rounded-lg transition-colors flex items-center justify-center shrink-0 cursor-pointer"
              aria-label="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* DESKTOP PERSISTENT SIDEBAR (lg:flex) */}
      <aside
        className={`hidden lg:flex bg-[#0b101b] border-r border-slate-800/80 flex-col h-screen sticky top-0 z-30 select-none transition-all duration-200 ease-in-out shrink-0 ${
          collapsed ? 'w-16' : 'w-64'
        }`}
        aria-label="Application Sidebar"
      >
        {/* Brand Header */}
        <div className="h-16 px-4 border-b border-slate-800/80 flex items-center justify-between">
          {!collapsed && (
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
                <Shield className="w-4 h-4" />
              </div>
              <div className="truncate">
                <h1 className="font-bold text-xs tracking-wider text-slate-100 uppercase font-mono leading-none">
                  SECUREOPS
                </h1>
                <p className="text-[9px] text-slate-400 font-mono tracking-wider mt-1">
                  AI SECURITY GATEWAY
                </p>
              </div>
            </div>
          )}

          {collapsed && (
            <div className="w-full flex justify-center">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                <Shield className="w-4 h-4" />
              </div>
            </div>
          )}

          <button
            onClick={() => setCollapsed(!collapsed)}
            className={`p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors cursor-pointer ${
              collapsed ? 'hidden' : 'block'
            }`}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        </div>

        {/* Toggle Expand in Collapsed Mode */}
        {collapsed && (
          <div className="pt-2 flex justify-center">
            <button
              onClick={() => setCollapsed(false)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors cursor-pointer"
              title="Expand sidebar"
              aria-label="Expand sidebar"
            >
              <PanelLeftOpen className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Navigation Groups */}
        {renderNavLinks(false)}

        {/* Desktop Footer Profile & Logout */}
        <div className="p-3 border-t border-slate-800/80 bg-[#090d16]/80">
          {!collapsed ? (
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2.5 overflow-hidden">
                <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-cyan-400 font-mono shrink-0">
                  {userRole ? userRole[0] : 'U'}
                </div>
                <div className="truncate">
                  <p className="text-xs font-medium text-slate-200 truncate">SecOps Admin</p>
                  <div className="flex items-center gap-1 mt-0.5">
                    <span className="text-[9px] text-cyan-400 font-mono uppercase bg-cyan-950/60 px-1 py-0.2 rounded border border-cyan-800/50 leading-tight">
                      {userRole}
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={logout}
                title="Disconnect / Logout"
                className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 rounded-lg transition-colors shrink-0 cursor-pointer"
                aria-label="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <div
                className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-cyan-400 font-mono"
                title={`User Role: ${userRole}`}
              >
                {userRole ? userRole[0] : 'U'}
              </div>
              <button
                onClick={logout}
                title="Disconnect / Logout"
                className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 rounded-lg transition-colors cursor-pointer"
                aria-label="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </aside>
    </>
  );
};
