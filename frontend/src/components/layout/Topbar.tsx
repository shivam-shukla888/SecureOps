import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Building2, Activity, Shield, LogOut, Menu } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { RoleEnum } from '../../types/api';

const PAGE_METADATA: Record<string, { title: string; description: string }> = {
  '/dashboard': {
    title: 'Overview',
    description: 'Real-time telemetry, risk decisions, and gateway activity',
  },
  '/gateway': {
    title: 'Request Gateway',
    description: 'AI prompt inspection, classification, and policy enforcement',
  },
  '/approvals': {
    title: 'Approval Center',
    description: 'Human-in-the-loop authorization for sensitive operations',
  },
  '/security-events': {
    title: 'Security Events',
    description: 'SIEM security event feed, attack detection, and alerts',
  },
  '/audit': {
    title: 'Audit Explorer',
    description: 'Immutable SHA-256 verified request audit logs',
  },
  '/executions': {
    title: 'Executions',
    description: 'Governed sandbox tool execution and dispatch logs',
  },
  '/tools': {
    title: 'Tool Governance',
    description: 'Authorized tools, schema validation, and risk policies',
  },
  '/tenants': {
    title: 'Tenants',
    description: 'Multi-tenant isolation and policy configurations',
  },
  '/rbac': {
    title: 'Users & Roles',
    description: 'Hierarchical role-based access control permissions',
  },
  '/credentials': {
    title: 'API Credentials',
    description: 'Hashed API key provisioning and lifecycle management',
  },
  '/health': {
    title: 'System Health',
    description: 'Gateway liveness, Redis, database, and rate limiter status',
  },
  '/settings': {
    title: 'Settings',
    description: 'Security parameters, AI provider fallback, and limits',
  },
};

interface TopbarProps {
  onOpenMobileNav?: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ onOpenMobileNav }) => {
  const location = useLocation();
  const { tenantId, setTenantId, userRole, setUserRole, logout } = useAuth();
  const [gatewayOnline, setGatewayOnline] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;

    const checkGatewayStatus = async () => {
      let isOnline = false;
      try {
        // Prefer /ready check since it verifies db, redis, and rate limiter
        const readyRes = await api.getReady();
        const rStatus = readyRes?.status?.toLowerCase();
        if (rStatus === 'ready' || rStatus === 'healthy' || rStatus === 'ok') {
          isOnline = true;
        }
      } catch {
        // Fallback to /health check
        try {
          const healthRes = await api.getHealth();
          const hStatus = healthRes?.status?.toLowerCase();
          if (hStatus === 'healthy' || hStatus === 'ready' || hStatus === 'ok') {
            isOnline = true;
          }
        } catch {
          isOnline = false;
        }
      }

      if (isMounted) {
        setGatewayOnline(isOnline);
      }
    };

    checkGatewayStatus();
    const interval = setInterval(checkGatewayStatus, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const currentPage = PAGE_METADATA[location.pathname] || {
    title: 'Security Console',
    description: 'SecureOps Enterprise AI Security Gateway',
  };

  return (
    <header
      className="h-16 bg-[#0b101b]/95 backdrop-blur-md border-b border-slate-800/80 px-3 sm:px-4 md:px-6 flex items-center justify-between sticky top-0 z-20 select-none"
      aria-label="Top Navigation Bar"
    >
      {/* Left: Mobile Hamburger & Page Title */}
      <div className="flex items-center gap-2.5 min-w-0 pr-2 sm:pr-4">
        {/* Mobile Hamburger Button */}
        <button
          onClick={onOpenMobileNav}
          className="lg:hidden p-2 min-h-[44px] min-w-[44px] rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800/70 transition-colors flex items-center justify-center shrink-0 cursor-pointer"
          aria-label="Open navigation menu"
          title="Open navigation menu"
        >
          <Menu className="w-5 h-5 text-cyan-400" />
        </button>

        <div className="flex flex-col justify-center min-w-0">
          <h2 className="text-xs sm:text-sm font-semibold text-white tracking-tight leading-tight truncate">
            {currentPage.title}
          </h2>
          <p className="text-[10px] sm:text-[11px] text-slate-400 font-mono truncate hidden sm:block">
            {currentPage.description}
          </p>
        </div>
      </div>

      {/* Right: Controls & Indicators */}
      <div className="flex items-center gap-1.5 sm:gap-2.5 md:gap-3 shrink-0">
        {/* Tenant Selector (Hidden on small mobile, visible sm+) */}
        <div className="hidden sm:flex items-center gap-1.5 md:gap-2 bg-[#111827] px-2 md:px-2.5 py-1.5 rounded-lg border border-slate-800 text-xs">
          <Building2 className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span className="text-slate-400 font-mono text-[10px] hidden md:inline">Tenant:</span>
          <select
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer text-[11px] sm:text-xs max-w-[110px] sm:max-w-none"
            aria-label="Select Tenant"
          >
            <option value="tenant_default" className="bg-slate-900 text-slate-200">
              Default (tenant_default)
            </option>
            <option value="tenant_acme" className="bg-slate-900 text-slate-200">
              Acme Corp (tenant_acme)
            </option>
            <option value="tenant_globex" className="bg-slate-900 text-slate-200">
              Globex (tenant_globex)
            </option>
          </select>
        </div>

        {/* Environment Badge */}
        <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-400 font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Production
        </div>

        {/* Gateway Status Indicator */}
        <div className="flex items-center gap-1.5 sm:gap-2 text-[11px] sm:text-xs font-mono px-2 sm:px-3 py-1.5 rounded-lg bg-[#111827] border border-slate-800">
          <Activity className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span className="text-slate-400 hidden lg:inline">Gateway:</span>
          {gatewayOnline ? (
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="hidden xs:inline">ONLINE</span>
            </span>
          ) : (
            <span className="text-rose-400 font-bold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
              <span className="hidden xs:inline">OFFLINE</span>
            </span>
          )}
        </div>

        {/* Role Selector */}
        <div className="flex items-center gap-1 sm:gap-1.5 bg-[#111827] px-2 sm:px-2.5 py-1.5 rounded-lg border border-slate-800 text-xs">
          <Shield className="w-3.5 h-3.5 text-purple-400 shrink-0" />
          <select
            value={userRole}
            onChange={(e) => setUserRole(e.target.value as RoleEnum)}
            className="bg-transparent text-purple-300 font-semibold focus:outline-none cursor-pointer text-[11px] sm:text-xs"
            aria-label="Current Role"
          >
            <option value="OWNER" className="bg-slate-900">OWNER</option>
            <option value="ADMIN" className="bg-slate-900">ADMIN</option>
            <option value="APPROVER" className="bg-slate-900">APPROVER</option>
            <option value="OPERATOR" className="bg-slate-900">OPERATOR</option>
            <option value="VIEWER" className="bg-slate-900">VIEWER</option>
          </select>
        </div>

        {/* Logout Action */}
        <button
          onClick={logout}
          title="Disconnect / Logout"
          aria-label="Logout"
          className="p-2 min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 rounded-lg border border-slate-800 transition-colors flex items-center justify-center cursor-pointer"
        >
          <LogOut className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  );
};
