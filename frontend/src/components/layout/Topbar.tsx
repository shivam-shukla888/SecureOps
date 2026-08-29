import React, { useState, useEffect } from 'react';
import { Building2, Activity, Shield, Bell, ChevronDown } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { RoleEnum } from '../../types/api';

export const Topbar: React.FC = () => {
  const { tenantId, setTenantId, userRole, setUserRole } = useAuth();
  const [gatewayOnline, setGatewayOnline] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;

    const checkGatewayStatus = async () => {
      let isOnline = false;
      try {
        // Prefer /ready check since it verifies db, redis, and rate limiter
        const readyRes = await api.getReady();
        if (readyRes && (readyRes.status === 'ready' || readyRes.status === 'healthy')) {
          isOnline = true;
        }
      } catch {
        // Fallback to /health check
        try {
          const healthRes = await api.getHealth();
          if (healthRes && (healthRes.status === 'healthy' || healthRes.status === 'ready')) {
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

  return (
    <header className="h-16 bg-[#0c121e]/90 backdrop-blur-md border-b border-slate-800/80 px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left: Tenant Selector */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 bg-[#141c2e] px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
          <Building2 className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400 font-mono text-[11px]">Tenant:</span>
          <select
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            className="bg-transparent text-slate-200 font-semibold focus:outline-none cursor-pointer"
          >
            <option value="tenant_default" className="bg-slate-900 text-slate-200">Default Tenant (tenant_default)</option>
            <option value="tenant_acme" className="bg-slate-900 text-slate-200">Acme Corp (tenant_acme)</option>
            <option value="tenant_globex" className="bg-slate-900 text-slate-200">Globex International (tenant_globex)</option>
          </select>
        </div>

        {/* Environment Badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] text-emerald-400 font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          development
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* System Health Indicator */}
        <div className="flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-lg bg-[#141c2e] border border-slate-800">
          <Activity className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-400">Gateway:</span>
          {gatewayOnline ? (
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              ONLINE
            </span>
          ) : (
            <span className="text-rose-400 font-bold flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              OFFLINE
            </span>
          )}
        </div>

        {/* Role Selector */}
        <div className="flex items-center gap-2 bg-[#141c2e] px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
          <Shield className="w-3.5 h-3.5 text-purple-400" />
          <span className="text-slate-400 font-mono text-[11px]">Role:</span>
          <select
            value={userRole}
            onChange={(e) => setUserRole(e.target.value as RoleEnum)}
            className="bg-transparent text-purple-300 font-semibold focus:outline-none cursor-pointer"
          >
            <option value="OWNER" className="bg-slate-900">OWNER</option>
            <option value="ADMIN" className="bg-slate-900">ADMIN</option>
            <option value="APPROVER" className="bg-slate-900">APPROVER</option>
            <option value="OPERATOR" className="bg-slate-900">OPERATOR</option>
            <option value="VIEWER" className="bg-slate-900">VIEWER</option>
          </select>
        </div>
      </div>
    </header>
  );
};
