import React, { useState } from 'react';
import { Key, Plus, RefreshCw, AlertTriangle, ShieldCheck, Copy, Check } from 'lucide-react';
import { api } from '../../services/api';
import { CreateCredentialResponse } from '../../types/api';
import { GlassCard } from '../layout/GlassCard';

export const CredentialsView: React.FC = () => {
  const [credName, setCredName] = useState('New Service Key');
  const [targetRole, setTargetRole] = useState('OPERATOR');
  const [loading, setLoading] = useState(false);
  const [newKeyData, setNewKeyData] = useState<CreateCredentialResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await api.createCredential({
        name: credName,
        role: targetRole,
      });
      setNewKeyData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to create credential.');
    } finally {
      setLoading(false);
    }
  };

  const copyKey = () => {
    if (newKeyData?.api_key) {
      navigator.clipboard.writeText(newKeyData.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6 font-mono text-xs">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          API Credential Lifecycle Management
          <Key className="w-5 h-5 text-cyan-400" />
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          SHA-256 hashed API key management supporting tenant-scoped creation, rotation, and revocation
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <GlassCard>
            <form onSubmit={handleCreate} className="space-y-4">
              <h3 className="text-sm font-bold text-white">Create New Tenant API Credential</h3>
              
              <div>
                <label className="block text-slate-400 mb-1">Credential Name</label>
                <input
                  type="text"
                  value={credName}
                  onChange={(e) => setCredName(e.target.value)}
                  className="w-full bg-[#0a0f1b] border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Role Assignment</label>
                <select
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  className="w-full bg-[#0a0f1b] border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none cursor-pointer"
                >
                  <option value="OWNER">OWNER</option>
                  <option value="ADMIN">ADMIN</option>
                  <option value="APPROVER">APPROVER</option>
                  <option value="OPERATOR">OPERATOR</option>
                  <option value="VIEWER">VIEWER</option>
                </select>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-emerald-600 text-white font-semibold flex items-center gap-1.5 transition-all disabled:opacity-50"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  <span>Generate Credential</span>
                </button>
              </div>
            </form>
          </GlassCard>

          {/* Modal / One-Time Display of Generated API Key */}
          {newKeyData && (
            <GlassCard glow="cyan">
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="font-bold text-emerald-400">Credential Generated Successfully</h3>
                  <span className="text-[10px] text-slate-400">{newKeyData.credential.credential_id}</span>
                </div>

                <div className="p-3 rounded-lg bg-[#0a0f1b] border border-amber-500/40 text-amber-300">
                  <p className="text-[11px] font-sans mb-2 font-medium">⚠️ Security Warning: {newKeyData.warning}</p>
                  <div className="flex items-center justify-between bg-[#111827] p-2.5 rounded border border-slate-800">
                    <code className="text-cyan-300 font-bold select-all break-all">{newKeyData.api_key}</code>
                    <button
                      onClick={copyKey}
                      className="ml-2 p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors shrink-0"
                    >
                      {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>
            </GlassCard>
          )}

          {error && (
            <GlassCard glow="rose">
              <div className="text-xs text-rose-400 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                <span>{error}</span>
              </div>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
};
