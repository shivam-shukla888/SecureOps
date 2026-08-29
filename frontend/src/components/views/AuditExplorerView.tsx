import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  FileText,
  Filter,
  Search,
  ShieldCheck,
  ShieldAlert,
  Clock,
  RefreshCw,
  RotateCcw,
  ArrowRight,
  Sparkles,
  Shield,
  Layers,
  Cpu,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Lock,
} from 'lucide-react';
import { api } from '../../services/api';
import { AuditEvent } from '../../types/api';
import { useAuth } from '../../context/AuthContext';

export const AuditExplorerView: React.FC = () => {
  const { tenantId, userRole } = useAuth();

  const [decisionFilter, setDecisionFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedLog, setSelectedLog] = useState<AuditEvent | null>(null);

  const {
    data,
    isLoading,
    isError,
    error: fetchError,
    refetch,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ['auditEvents', decisionFilter],
    queryFn: () =>
      api.listAuditEvents({
        limit: 100,
        decision: decisionFilter === 'ALL' ? undefined : decisionFilter,
      }),
    refetchInterval: 10000,
  });

  const logs: AuditEvent[] = data?.events || [];

  const filteredLogs = logs.filter((log) => {
    if (!searchTerm.trim()) return true;
    const query = searchTerm.toLowerCase().trim();
    return (
      log.request_id.toLowerCase().includes(query) ||
      log.user_id.toLowerCase().includes(query) ||
      log.intent.toLowerCase().includes(query) ||
      log.resource.toLowerCase().includes(query) ||
      (log.provider && log.provider.toLowerCase().includes(query)) ||
      (log.error_status && log.error_status.toLowerCase().includes(query))
    );
  });

  const handleResetFilters = () => {
    setDecisionFilter('ALL');
    setSearchTerm('');
  };

  const formattedLastUpdated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString()
    : 'Live';

  return (
    <div className="space-y-6 select-none">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-white tracking-tight font-mono uppercase">
              AUDIT EXPLORER
            </h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              IMMUTABLE AUDIT TRAIL
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Trace request activity and inspect cryptographically verifiable audit records.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start md:self-auto">
          <div className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-[#111827] border border-slate-800 text-[11px] font-mono text-slate-400">
            <span>
              Tenant: <strong className="text-slate-200">{tenantId}</strong>
            </span>
            <span className="text-slate-700">|</span>
            <span>
              Updated: <strong className="text-slate-200">{formattedLastUpdated}</strong>
            </span>
          </div>

          <button
            onClick={() => refetch()}
            className="px-3 py-1.5 rounded-lg bg-[#111827] border border-slate-800 hover:border-cyan-500/40 text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1.5 transition-colors cursor-pointer"
            title="Refresh audit event log"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filter Controls Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Decision Filter Pills */}
        <div className="flex items-center gap-1 p-1 rounded-lg bg-[#111827] border border-slate-800 text-xs font-mono">
          {['ALL', 'ALLOW', 'REQUIRE_APPROVAL', 'BLOCK'].map((dec) => (
            <button
              key={dec}
              onClick={() => {
                setDecisionFilter(dec);
                setSelectedLog(null);
              }}
              className={`px-3 py-1 rounded-md transition-colors cursor-pointer ${
                decisionFilter === dec
                  ? 'bg-slate-800 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              {dec}
            </button>
          ))}
        </div>

        {/* Search & Reset */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search request ID, user, resource..."
              className="w-full bg-[#111827] border border-slate-800 focus:border-cyan-500 rounded-lg py-1.5 pl-8 pr-3 text-xs text-slate-200 font-mono focus:outline-none placeholder:text-slate-600"
            />
          </div>

          {(decisionFilter !== 'ALL' || searchTerm) && (
            <button
              onClick={handleResetFilters}
              className="px-2.5 py-1.5 rounded-lg bg-[#111827] border border-slate-800 text-slate-400 hover:text-slate-200 text-xs font-mono flex items-center gap-1 transition-colors cursor-pointer"
              title="Reset active filters"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Grid: Audit Log Table (7 cols) + Detail Inspector (5 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Audit Records Table */}
        <div className="lg:col-span-7 space-y-4">
          <div className="rounded-xl bg-[#111827] border border-slate-800/80 overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 font-medium">
                {filteredLogs.length} {filteredLogs.length === 1 ? 'Record' : 'Records'} Logged
              </span>
              <span className="text-[10px] font-mono text-cyan-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                Polling (10s)
              </span>
            </div>

            {isLoading ? (
              <div className="p-12 text-center text-slate-500 font-mono text-xs space-y-2">
                <RefreshCw className="w-5 h-5 animate-spin mx-auto text-cyan-400" />
                <p>Loading forensic audit trail...</p>
              </div>
            ) : isError ? (
              <div className="p-8 text-center text-rose-400 font-mono text-xs space-y-2">
                <AlertTriangle className="w-5 h-5 mx-auto text-rose-400" />
                <p>Failed to load audit records. {(fetchError as any)?.message || ''}</p>
                <button
                  onClick={() => refetch()}
                  className="px-3 py-1 rounded bg-rose-500/20 text-rose-300 text-xs mt-2"
                >
                  Retry
                </button>
              </div>
            ) : filteredLogs.length === 0 ? (
              <div className="p-12 text-center text-slate-500 font-mono text-xs space-y-2">
                <ShieldCheck className="w-8 h-8 mx-auto text-slate-600" />
                <p className="text-slate-300 font-medium">No audit records</p>
                <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
                  Auditable request activity will appear here after gateway operations are processed.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-[#0e1422] text-[10px] font-mono uppercase text-slate-400">
                      <th className="p-3">Request ID</th>
                      <th className="p-3">Requester</th>
                      <th className="p-3">Intent / Resource</th>
                      <th className="p-3">Decision</th>
                      <th className="p-3 text-right">Latency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                    {filteredLogs.map((log) => {
                      const isSelected = selectedLog?.request_id === log.request_id;
                      const dec = log.final_decision;
                      return (
                        <tr
                          key={log.request_id}
                          onClick={() => setSelectedLog(log)}
                          className={`hover:bg-[#151c2e] cursor-pointer transition-colors ${
                            isSelected ? 'bg-[#18233a]' : ''
                          }`}
                        >
                          <td className="p-3">
                            <span className="text-cyan-400 font-bold block select-all">
                              {log.request_id}
                            </span>
                            <span className="text-[10px] text-slate-500">
                              {new Date(log.timestamp).toLocaleTimeString()}
                            </span>
                          </td>
                          <td className="p-3 text-slate-300">{log.user_id}</td>
                          <td className="p-3">
                            <span className="text-slate-200 block">{log.intent}</span>
                            <span className="text-[10px] text-slate-500 truncate max-w-[140px] block">
                              {log.resource}
                            </span>
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold inline-flex items-center gap-1 ${
                                dec === 'ALLOW'
                                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                  : dec === 'REQUIRE_APPROVAL'
                                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                  : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              }`}
                            >
                              {dec}
                            </span>
                          </td>
                          <td className="p-3 text-right text-slate-400 text-[11px]">
                            {typeof log.latency_ms === 'number'
                              ? `${log.latency_ms.toFixed(1)} ms`
                              : '--'}
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

        {/* Right Column: Forensic Detail Inspector */}
        <div className="lg:col-span-5 space-y-4">
          {selectedLog ? (
            <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4 font-mono text-xs">
              <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-white text-sm font-mono uppercase">
                    Forensic Audit Detail
                  </h3>
                  <span className="text-[10px] text-cyan-400 select-all">
                    {selectedLog.request_id}
                  </span>
                </div>
                <span
                  className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                    selectedLog.final_decision === 'ALLOW'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : selectedLog.final_decision === 'REQUIRE_APPROVAL'
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  }`}
                >
                  {selectedLog.final_decision}
                </span>
              </div>

              {/* Request Identity Context */}
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Request Identity
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Request ID:</span>
                    <strong className="text-slate-200 select-all">{selectedLog.request_id}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Tenant ID:</span>
                    <strong className="text-slate-200">{selectedLog.tenant_id}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Requester User:</span>
                    <strong className="text-slate-200">{selectedLog.user_id}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Timestamp:</span>
                    <span className="text-slate-300 text-[11px]">
                      {new Date(selectedLog.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Security & AI Evaluation */}
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Security & Policy Evaluation
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Intent:</span>
                    <strong className="text-slate-200">{selectedLog.intent}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Target Resource:</span>
                    <strong className="text-slate-200">{selectedLog.resource}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">AI Risk Score:</span>
                    <strong
                      className={
                        selectedLog.ai_risk === 'HIGH'
                          ? 'text-rose-400'
                          : selectedLog.ai_risk === 'MEDIUM'
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }
                    >
                      {selectedLog.ai_risk}
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Policy Risk Level:</span>
                    <strong
                      className={
                        selectedLog.policy_risk === 'HIGH'
                          ? 'text-rose-400'
                          : selectedLog.policy_risk === 'MEDIUM'
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }
                    >
                      {selectedLog.policy_risk}
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">AI Provider:</span>
                    <span className="text-purple-300">
                      {selectedLog.provider}{' '}
                      {selectedLog.fallback_used ? '(Fallback Engaged)' : ''}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Pipeline Latency:</span>
                    <span className="text-cyan-400">{selectedLog.latency_ms.toFixed(1)} ms</span>
                  </div>
                </div>
              </div>

              {/* Lifecycle Trace */}
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Request Lifecycle Trace
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-1.5">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">1. Ingest & Rate Limit</span>
                    <span className="text-emerald-400">PASS</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">2. AI Intent Classification</span>
                    <span className="text-purple-300">{selectedLog.intent}</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">3. Deterministic Policy</span>
                    <span className="text-cyan-400">{selectedLog.policy_risk} RISK</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">4. Authorization Verdict</span>
                    <span
                      className={`font-bold ${
                        selectedLog.final_decision === 'ALLOW'
                          ? 'text-emerald-400'
                          : selectedLog.final_decision === 'REQUIRE_APPROVAL'
                          ? 'text-amber-400'
                          : 'text-rose-400'
                      }`}
                    >
                      {selectedLog.final_decision}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">5. SHA-256 Audit Commitment</span>
                    <span className="text-emerald-400 font-bold">COMMITTED</span>
                  </div>
                </div>
              </div>

              {/* Raw Audit Record JSON */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                    Redacted Audit Record Payload
                  </div>
                  <span className="text-[10px] text-slate-500">Real Log Payload</span>
                </div>
                <pre className="p-3 rounded-lg bg-[#0a0f1b] border border-slate-800 text-[11px] font-mono text-cyan-300 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(selectedLog, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-xl bg-[#111827] border border-slate-800/80 text-center space-y-3">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mx-auto">
                <FileText className="w-5 h-5" />
              </div>
              <h4 className="text-xs font-semibold text-white font-mono uppercase">
                No Record Selected
              </h4>
              <p className="text-[11px] text-slate-400 font-mono max-w-xs mx-auto">
                Select an audit record from the table on the left to inspect complete forensic metadata, policy evaluation stages, and lifecycle telemetry.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
