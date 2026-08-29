import React, { useState } from 'react';
import {
  Key,
  Plus,
  RefreshCw,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  Copy,
  Check,
  RotateCcw,
  Lock,
  Trash2,
  Search,
  Filter,
  Info,
  Layers,
  ArrowRight,
  Shield,
  Eye,
  EyeOff,
} from 'lucide-react';
import { api, APIError } from '../../services/api';
import { CreateCredentialResponse, APICredentialRecord, RoleEnum } from '../../types/api';
import { useAuth } from '../../context/AuthContext';

interface DisplayCredential {
  credential_id: string;
  name: string;
  user_id: string;
  role: RoleEnum;
  tenant_id: string;
  status: 'ACTIVE' | 'REVOKED';
  created_at: string;
  revoked_at?: string | null;
}

export const CredentialsView: React.FC = () => {
  const { tenantId, userRole, userId: currentUserId } = useAuth();

  const canManage = userRole === 'OWNER' || userRole === 'ADMIN';

  const [credName, setCredName] = useState('');
  const [targetUserId, setTargetUserId] = useState(currentUserId || 'operator_sarah');
  const [targetRole, setTargetRole] = useState<RoleEnum>('OPERATOR');
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // One-time secret state
  const [oneTimeSecretData, setOneTimeSecretData] = useState<CreateCredentialResponse | null>(null);

  // Revoke confirmation modal state
  const [revokingCred, setRevokingCred] = useState<DisplayCredential | null>(null);

  // Credential selection for detail inspector
  const [selectedCred, setSelectedCred] = useState<DisplayCredential | null>(null);

  // Filters
  const [roleFilter, setRoleFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Local inventory state of generated/tracked credentials
  const [credentials, setCredentials] = useState<DisplayCredential[]>([
    {
      credential_id: 'cred_default_admin',
      name: 'Primary Security Gateway Key',
      user_id: currentUserId || 'admin_user',
      role: 'ADMIN',
      tenant_id: tenantId,
      status: 'ACTIVE',
      created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
    },
  ]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!credName.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await api.createCredential({
        name: credName.trim(),
        user_id: targetUserId.trim() || undefined,
        role: targetRole,
      });

      setOneTimeSecretData(res);

      const newRecord: DisplayCredential = {
        credential_id: res.credential.credential_id,
        name: res.credential.name,
        user_id: res.credential.user_id,
        role: res.credential.role,
        tenant_id: res.credential.tenant_id,
        status: 'ACTIVE',
        created_at: res.credential.created_at,
      };

      setCredentials((prev) => [newRecord, ...prev]);
      setSelectedCred(newRecord);
      setCredName('');
    } catch (err: any) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError(err.message || 'Failed to generate API credential.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeConfirm = async () => {
    if (!revokingCred) return;

    setActionLoading(true);
    setError(null);

    try {
      await api.revokeCredential(revokingCred.credential_id);

      setCredentials((prev) =>
        prev.map((c) =>
          c.credential_id === revokingCred.credential_id
            ? { ...c, status: 'REVOKED', revoked_at: new Date().toISOString() }
            : c
        )
      );

      if (selectedCred?.credential_id === revokingCred.credential_id) {
        setSelectedCred({
          ...selectedCred,
          status: 'REVOKED',
          revoked_at: new Date().toISOString(),
        });
      }

      setRevokingCred(null);
    } catch (err: any) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError(err.message || 'Failed to revoke API credential.');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleRotate = async (cred: DisplayCredential) => {
    setActionLoading(true);
    setError(null);

    try {
      const res = await api.rotateCredential(cred.credential_id);
      setOneTimeSecretData(res);

      setCredentials((prev) =>
        prev.map((c) =>
          c.credential_id === cred.credential_id
            ? { ...c, status: 'ACTIVE', created_at: res.credential.created_at }
            : c
        )
      );
    } catch (err: any) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError(err.message || 'Failed to rotate API credential.');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const copySecret = () => {
    if (oneTimeSecretData?.api_key) {
      navigator.clipboard.writeText(oneTimeSecretData.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const filteredCredentials = credentials.filter((c) => {
    const matchesRole = roleFilter === 'ALL' || c.role === roleFilter;
    const query = searchTerm.toLowerCase().trim();
    const matchesSearch =
      !query ||
      c.name.toLowerCase().includes(query) ||
      c.credential_id.toLowerCase().includes(query) ||
      c.user_id.toLowerCase().includes(query);
    return matchesRole && matchesSearch;
  });

  return (
    <div className="space-y-4 sm:space-y-6 select-none max-w-full">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 pb-2 border-b border-slate-800/80">
        <div className="min-w-0">
          <div className="flex items-center gap-2 sm:gap-2.5 flex-wrap">
            <h1 className="text-lg sm:text-xl font-bold text-white tracking-tight font-mono uppercase truncate">
              API CREDENTIALS
            </h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shrink-0">
              SHA-256 VAULT
            </span>
          </div>
          <p className="text-[11px] sm:text-xs text-slate-400 font-mono mt-1">
            Manage authentication credentials and access identity across SecureOps.
          </p>
        </div>

        <div className="flex items-center gap-2 sm:gap-3 self-start sm:self-auto shrink-0">
          <div className="flex items-center gap-2 sm:gap-3 px-2.5 sm:px-3 py-1.5 rounded-lg bg-[#111827] border border-slate-800 text-[10px] sm:text-[11px] font-mono text-slate-400">
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

      {/* RBAC Notice if non-admin */}
      {!canManage && (
        <div className="p-3 sm:p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-mono flex items-center gap-2.5">
          <Info className="w-4 h-4 text-amber-400 shrink-0" />
          <span className="break-words">
            Current role <strong className="uppercase">{userRole}</strong> has read-only credential viewing permissions. <strong>ADMIN</strong> or <strong>OWNER</strong> role is required to generate or revoke keys.
          </span>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="p-3 sm:p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-mono flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span className="break-words">{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-slate-400 hover:text-white text-xs px-2 min-h-[36px] flex items-center"
          >
            ✕
          </button>
        </div>
      )}

      {/* ONE-TIME SECRET DIALOG (CRITICAL SECURITY UX) */}
      {oneTimeSecretData && (
        <div className="p-4 sm:p-5 rounded-xl bg-[#0f172a] border-2 border-emerald-500/60 shadow-xl space-y-4 font-mono text-xs max-w-full">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 gap-2 flex-wrap">
            <div className="flex items-center gap-2 min-w-0">
              <Key className="w-5 h-5 text-emerald-400 shrink-0" />
              <div className="min-w-0">
                <h3 className="font-bold text-white text-xs sm:text-sm uppercase truncate">
                  Credential Generated Successfully
                </h3>
                <span className="text-[10px] text-slate-400 break-all block">
                  ID: {oneTimeSecretData.credential.credential_id}
                </span>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shrink-0">
              {oneTimeSecretData.status.toUpperCase()}
            </span>
          </div>

          <div className="p-3.5 sm:p-4 rounded-lg bg-amber-950/30 border border-amber-500/40 text-amber-300 space-y-2">
            <div className="flex items-start gap-2 font-bold text-xs">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <span>Critical Security Warning: One-Time Secret Display</span>
            </div>
            <p className="text-[11px] leading-relaxed text-amber-200/90 font-sans break-words">
              Store this secret securely now. SecureOps stores only an irreversible SHA-256 hash and cannot recover or display this secret again after closing this panel.
            </p>
          </div>

          <div className="space-y-1.5">
            <label className="block text-slate-400 text-[11px]">API Key Secret</label>
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
              <div className="flex-1 p-3 rounded-lg bg-[#0a0f1b] border border-cyan-500/40 text-cyan-300 font-bold font-mono text-xs select-all break-all overflow-x-auto">
                {oneTimeSecretData.api_key}
              </div>
              <button
                onClick={copySecret}
                className="px-4 py-2.5 sm:py-3 min-h-[44px] sm:min-h-0 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold flex items-center justify-center gap-1.5 transition-colors shrink-0 cursor-pointer"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
                <span>{copied ? 'Copied!' : 'Copy Secret'}</span>
              </button>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={() => setOneTimeSecretData(null)}
              className="px-4 py-2.5 sm:py-2 min-h-[44px] sm:min-h-0 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold transition-colors cursor-pointer w-full sm:w-auto text-center"
            >
              Done & Dismiss Secret
            </button>
          </div>
        </div>
      )}

      {/* REVOKE CONFIRMATION MODAL */}
      {revokingCred && (
        <div className="p-4 sm:p-5 rounded-xl bg-[#1e1014] border-2 border-rose-500/60 shadow-xl space-y-4 font-mono text-xs max-w-full">
          <div className="flex items-center gap-2 text-rose-400 font-bold text-xs sm:text-sm uppercase">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <span>Confirm Credential Revocation</span>
          </div>

          <p className="text-slate-300 text-[11px] font-sans leading-relaxed break-words">
            Are you sure you want to revoke credential <strong className="text-white font-mono break-all">{revokingCred.name}</strong> ({revokingCred.credential_id})? Existing AI agents or services using this credential will immediately lose access to the SecureOps gateway.
          </p>

          <div className="flex flex-col-reverse sm:flex-row justify-end gap-2.5 sm:gap-3 pt-2">
            <button
              onClick={() => setRevokingCred(null)}
              disabled={actionLoading}
              className="px-4 py-2.5 sm:py-1.5 min-h-[44px] sm:min-h-0 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors cursor-pointer text-center"
            >
              Cancel
            </button>
            <button
              onClick={handleRevokeConfirm}
              disabled={actionLoading}
              className="px-4 py-2.5 sm:py-1.5 min-h-[44px] sm:min-h-0 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {actionLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
              <span>Revoke Immediately</span>
            </button>
          </div>
        </div>
      )}

      {/* Main Grid: Generator/Filters on Left (5 cols on lg) + Credential List/Details on Right (7 cols on lg) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6 items-start">
        {/* Left Column: Generator Form & Architectural Info */}
        <div className="lg:col-span-5 space-y-4 w-full">
          <div className="p-4 sm:p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 sm:pb-3">
              <div className="flex items-center gap-2">
                <Plus className="w-4 h-4 text-cyan-400 shrink-0" />
                <h2 className="text-xs sm:text-sm font-semibold text-white uppercase">
                  Issue API Credential
                </h2>
              </div>
              <span className="text-[10px] text-slate-500 uppercase">Tenant Vault</span>
            </div>

            <form onSubmit={handleCreate} className="space-y-3.5 sm:space-y-4">
              <div>
                <label className="block text-slate-400 mb-1.5 font-medium">
                  Credential Name / Label
                </label>
                <input
                  type="text"
                  value={credName}
                  onChange={(e) => setCredName(e.target.value)}
                  placeholder="e.g. Production Agent Service Key"
                  disabled={!canManage || loading}
                  className="w-full bg-[#0a0f1b] border border-slate-800 focus:border-cyan-500 rounded-lg py-2.5 sm:py-2 px-3 text-xs text-slate-200 focus:outline-none disabled:opacity-50 min-h-[44px] sm:min-h-0"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1.5 font-medium">
                  Assigned User / Service Principal
                </label>
                <input
                  type="text"
                  value={targetUserId}
                  onChange={(e) => setTargetUserId(e.target.value)}
                  placeholder="e.g. operator_sarah"
                  disabled={!canManage || loading}
                  className="w-full bg-[#0a0f1b] border border-slate-800 focus:border-cyan-500 rounded-lg py-2.5 sm:py-2 px-3 text-xs text-slate-200 focus:outline-none disabled:opacity-50 min-h-[44px] sm:min-h-0"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1.5 font-medium">
                  Role Assignment (RBAC Scope)
                </label>
                <select
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value as RoleEnum)}
                  disabled={!canManage || loading}
                  className="w-full bg-[#0a0f1b] border border-slate-800 focus:border-cyan-500 rounded-lg py-2.5 sm:py-2 px-3 text-xs text-slate-200 focus:outline-none cursor-pointer disabled:opacity-50 min-h-[44px] sm:min-h-0"
                >
                  <option value="OPERATOR">OPERATOR (Standard Gateway Access)</option>
                  <option value="APPROVER">APPROVER (Can Authorize HITL Tickets)</option>
                  <option value="ADMIN">ADMIN (Full Tenant Management)</option>
                  <option value="OWNER">OWNER (Full System Privilege)</option>
                  <option value="VIEWER">VIEWER (Read-Only Telemetry)</option>
                </select>
              </div>

              <div className="pt-2 border-t border-slate-800 flex justify-end">
                <button
                  type="submit"
                  disabled={!canManage || loading || !credName.trim()}
                  className="px-4 py-2.5 sm:py-2 min-h-[44px] sm:min-h-0 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50 cursor-pointer w-full sm:w-auto"
                >
                  {loading ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Plus className="w-3.5 h-3.5" />
                  )}
                  <span>Generate Key</span>
                </button>
              </div>
            </form>
          </div>

          {/* Vault Security Info */}
          <div className="p-3.5 sm:p-4 rounded-xl bg-[#0e1422] border border-slate-800/80 text-slate-400 text-xs flex items-start gap-2.5 font-mono">
            <Lock className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
            <div className="text-[11px] leading-relaxed">
              <strong className="text-slate-200 block mb-0.5">
                Cryptographic Key Protection
              </strong>
              API credentials authenticate incoming requests. Keys are canonicalized, single-Bearer stripped, and evaluated against salted SHA-256 hashes on the gateway.
            </div>
          </div>
        </div>

        {/* Right Column: Inventory & Detail Inspector */}
        <div className="lg:col-span-7 space-y-4 w-full">
          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 font-mono text-xs">
            <div className="flex items-center gap-1 p-1 rounded-lg bg-[#111827] border border-slate-800 overflow-x-auto max-w-full custom-scrollbar">
              {['ALL', 'OWNER', 'ADMIN', 'APPROVER', 'OPERATOR', 'VIEWER'].map((r) => (
                <button
                  key={r}
                  onClick={() => setRoleFilter(r)}
                  className={`px-3 py-2 sm:py-1 min-h-[44px] sm:min-h-0 rounded-md transition-colors cursor-pointer whitespace-nowrap flex items-center shrink-0 ${
                    roleFilter === r
                      ? 'bg-slate-800 text-white font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>

            <div className="relative flex-1 sm:w-48">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search keys, users..."
                className="w-full bg-[#111827] border border-slate-800 focus:border-cyan-500 rounded-lg py-2 sm:py-1.5 pl-8 pr-3 text-xs text-slate-200 focus:outline-none placeholder:text-slate-600 min-h-[44px] sm:min-h-0"
              />
            </div>
          </div>

          {/* Credential Inventory Table */}
          <div className="rounded-xl bg-[#111827] border border-slate-800/80 overflow-hidden font-mono text-xs max-w-full">
            <div className="p-3.5 sm:p-4 border-b border-slate-800 flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">
                {filteredCredentials.length} {filteredCredentials.length === 1 ? 'Credential' : 'Credentials'} Listed
              </span>
              <span className="text-[10px] text-cyan-400 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                Active Tenant Scoping
              </span>
            </div>

            {filteredCredentials.length === 0 ? (
              <div className="p-8 sm:p-12 text-center text-slate-500 space-y-2">
                <Key className="w-8 h-8 mx-auto text-slate-600" />
                <p className="text-slate-300 font-medium">No credentials found</p>
                <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
                  API credentials issued to SecureOps users and agents will appear here.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto max-w-full">
                <table className="w-full text-left border-collapse min-w-[500px] sm:min-w-0">
                  <thead>
                    <tr className="border-b border-slate-800 bg-[#0e1422] text-[10px] uppercase text-slate-400">
                      <th className="p-3">Label / ID</th>
                      <th className="p-3">User</th>
                      <th className="p-3">Role</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredCredentials.map((cred) => {
                      const isSelected = selectedCred?.credential_id === cred.credential_id;
                      return (
                        <tr
                          key={cred.credential_id}
                          onClick={() => setSelectedCred(cred)}
                          className={`hover:bg-[#151c2e] cursor-pointer transition-colors ${
                            isSelected ? 'bg-[#18233a]' : ''
                          }`}
                        >
                          <td className="p-3">
                            <span className="text-slate-200 font-bold block break-words">{cred.name}</span>
                            <span className="text-[10px] text-cyan-400 block select-all break-all">
                              {cred.credential_id}
                            </span>
                          </td>
                          <td className="p-3 text-slate-300 break-all">{cred.user_id}</td>
                          <td className="p-3">
                            <span className="text-cyan-300 font-semibold">{cred.role}</span>
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                                cred.status === 'ACTIVE'
                                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                  : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              }`}
                            >
                              {cred.status}
                            </span>
                          </td>
                          <td className="p-3 text-right">
                            <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                              {canManage && cred.status === 'ACTIVE' && (
                                <button
                                  onClick={() => setRevokingCred(cred)}
                                  className="p-2 rounded hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-colors min-h-[36px] min-w-[36px] flex items-center justify-center cursor-pointer"
                                  title="Revoke Credential"
                                  aria-label={`Revoke ${cred.name}`}
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              )}
                              <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Selected Credential Detail */}
          {selectedCred && (
            <div className="p-4 sm:p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-3 font-mono text-xs">
              <div className="border-b border-slate-800 pb-2 flex items-center justify-between gap-2 flex-wrap">
                <div>
                  <h4 className="text-xs font-semibold text-white uppercase">
                    Credential Metadata
                  </h4>
                  <span className="text-[10px] text-cyan-400 select-all break-all">
                    {selectedCred.credential_id}
                  </span>
                </div>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                    selectedCred.status === 'ACTIVE'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  }`}
                >
                  {selectedCred.status}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 sm:gap-3">
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-400 block">NAME</span>
                  <strong className="text-slate-200 block truncate break-words">{selectedCred.name}</strong>
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-400 block">USER</span>
                  <strong className="text-slate-200 block truncate break-all">{selectedCred.user_id}</strong>
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-400 block">ROLE</span>
                  <strong className="text-cyan-300 block">{selectedCred.role}</strong>
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-400 block">HASH STORAGE</span>
                  <strong className="text-emerald-400 block">SHA-256 Hashed</strong>
                </div>
              </div>

              {canManage && selectedCred.status === 'ACTIVE' && (
                <div className="pt-2 border-t border-slate-800 flex flex-col sm:flex-row justify-end gap-2.5 sm:gap-3">
                  <button
                    onClick={() => handleRotate(selectedCred)}
                    disabled={actionLoading}
                    className="px-3 py-2 sm:py-1.5 min-h-[44px] sm:min-h-0 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Rotate Key</span>
                  </button>
                  <button
                    onClick={() => setRevokingCred(selectedCred)}
                    disabled={actionLoading}
                    className="px-3 py-2 sm:py-1.5 min-h-[44px] sm:min-h-0 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Revoke</span>
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
