import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, Filter, Search, ShieldCheck, ShieldAlert, Clock } from 'lucide-react';
import { api } from '../../services/api';
import { AuditEvent } from '../../types/api';
import { GlassCard } from '../layout/GlassCard';

export const AuditExplorerView: React.FC = () => {
  const [decisionFilter, setDecisionFilter] = useState<string>('ALL');
  const [selectedLog, setSelectedLog] = useState<AuditEvent | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['auditEvents', decisionFilter],
    queryFn: () => api.listAuditEvents(100),
    refetchInterval: 10000,
  });

  const logs: AuditEvent[] = data?.events || [];

  const filteredLogs = logs.filter((l) => {
    return decisionFilter === 'ALL' || l.final_decision === decisionFilter;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            Audit Explorer
            <FileText className="w-5 h-5 text-cyan-400" />
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Immutable, redacted security audit logs partitioned by tenant
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-2 bg-[#141c2e] px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
          <Filter className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400 font-mono text-[11px]">Decision:</span>
          <select
            value={decisionFilter}
            onChange={(e) => setDecisionFilter(e.target.value)}
            className="bg-transparent text-slate-200 font-mono font-semibold focus:outline-none cursor-pointer"
          >
            <option value="ALL" className="bg-slate-900">ALL DECISIONS</option>
            <option value="ALLOW" className="bg-slate-900">ALLOW</option>
            <option value="REQUIRE_APPROVAL" className="bg-slate-900">REQUIRE_APPROVAL</option>
            <option value="BLOCK" className="bg-slate-900">BLOCK</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <GlassCard className="p-0 overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">Total Logged Audit Events ({filteredLogs.length})</span>
            </div>

            {isLoading ? (
              <div className="p-8 text-center text-slate-500 font-mono text-xs">Loading audit logs...</div>
            ) : filteredLogs.length === 0 ? (
              <div className="p-8 text-center text-slate-500 font-mono text-xs">No audit logs recorded yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-[#0d1322] text-[10px] font-mono uppercase text-slate-400">
                      <th className="p-3">Request ID</th>
                      <th className="p-3">User</th>
                      <th className="p-3">Intent</th>
                      <th className="p-3">Decision</th>
                      <th className="p-3 text-right">Latency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                    {filteredLogs.map((log) => (
                      <tr
                        key={log.request_id}
                        onClick={() => setSelectedLog(log)}
                        className="hover:bg-[#161e31] cursor-pointer transition-colors"
                      >
                        <td className="p-3 text-cyan-400 font-bold">{log.request_id}</td>
                        <td className="p-3 text-slate-300">{log.user_id}</td>
                        <td className="p-3 text-slate-300">{log.intent}</td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              log.final_decision === 'ALLOW'
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                : log.final_decision === 'REQUIRE_APPROVAL'
                                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                            }`}
                          >
                            {log.final_decision}
                          </span>
                        </td>
                        <td className="p-3 text-right text-slate-400 text-[11px]">{log.latency_ms.toFixed(1)} ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </GlassCard>
        </div>

        {/* Sidebar Log Detail */}
        <div>
          {selectedLog ? (
            <GlassCard glow="cyan">
              <div className="space-y-3 font-mono text-xs">
                <div className="border-b border-slate-800 pb-2">
                  <h3 className="font-bold text-white">Audit Event Detail</h3>
                  <span className="text-[10px] text-cyan-400">{selectedLog.request_id}</span>
                </div>
                <pre className="p-3 rounded-lg bg-[#0a0f1b] border border-slate-800 whitespace-pre-wrap text-[11px] text-cyan-300">
                  {JSON.stringify(selectedLog, null, 2)}
                </pre>
              </div>
            </GlassCard>
          ) : (
            <GlassCard>
              <div className="p-8 text-center text-slate-500 font-mono text-xs">
                Select an audit record from the table to view redacted JSON payload.
              </div>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
};
