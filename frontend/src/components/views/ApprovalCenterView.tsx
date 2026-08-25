import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckSquare, CheckCircle2, XCircle, Clock, AlertTriangle, Shield, UserCheck, Search, Filter } from 'lucide-react';
import { api } from '../../services/api';
import { ApprovalTicket } from '../../types/api';
import { GlassCard } from '../layout/GlassCard';

export const ApprovalCenterView: React.FC = () => {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [selectedTicket, setSelectedTicket] = useState<ApprovalTicket | null>(null);
  const [actionError, setActionError] = useState<string>('');
  const [approverId, setApproverId] = useState<string>('security_officer_bob');

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['approvals', statusFilter],
    queryFn: () => api.listApprovals(statusFilter === 'ALL' ? undefined : statusFilter),
    refetchInterval: 8000,
  });

  const approveMutation = useMutation({
    mutationFn: ({ id, approver }: { id: string; approver: string }) => api.approveRequest(id, approver),
    onSuccess: () => {
      setActionError('');
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
      setSelectedTicket(null);
    },
    onError: (err: any) => {
      setActionError(err.message || 'Failed to approve request.');
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, approver }: { id: string; approver: string }) => api.rejectRequest(id, approver),
    onSuccess: () => {
      setActionError('');
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
      setSelectedTicket(null);
    },
    onError: (err: any) => {
      setActionError(err.message || 'Failed to reject request.');
    },
  });

  const tickets = data?.approvals || [];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            Human-In-The-Loop Approval Center
            <CheckSquare className="w-5 h-5 text-cyan-400" />
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Review and authorize time-bound security approval tickets
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-2 bg-[#141c2e] px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
          <Filter className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400 font-mono text-[11px]">Filter Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-transparent text-slate-200 font-mono font-semibold focus:outline-none cursor-pointer"
          >
            <option value="ALL" className="bg-slate-900">ALL TICKETS</option>
            <option value="PENDING" className="bg-slate-900">PENDING</option>
            <option value="APPROVED" className="bg-slate-900">APPROVED</option>
            <option value="REJECTED" className="bg-slate-900">REJECTED</option>
            <option value="EXPIRED" className="bg-slate-900">EXPIRED</option>
          </select>
        </div>
      </div>

      {actionError && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{actionError}</span>
          </div>
          <button onClick={() => setActionError('')} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Main Table & Details Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <GlassCard className="p-0 overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">Showing {tickets.length} Tickets</span>
              <span className="text-[11px] font-mono text-cyan-400">Auto-refreshing every 8s</span>
            </div>

            {isLoading ? (
              <div className="p-8 text-center text-slate-500 font-mono text-xs">Loading tickets...</div>
            ) : tickets.length === 0 ? (
              <div className="p-8 text-center text-slate-500 font-mono text-xs">No approval tickets found.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-[#0d1322] text-[10px] font-mono uppercase text-slate-400">
                      <th className="p-3">Ticket ID</th>
                      <th className="p-3">Requester</th>
                      <th className="p-3">Intent</th>
                      <th className="p-3">Risk</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                    {tickets.map((t) => (
                      <tr
                        key={t.approval_id}
                        onClick={() => setSelectedTicket(t)}
                        className={`hover:bg-[#161e31] cursor-pointer transition-colors ${
                          selectedTicket?.approval_id === t.approval_id ? 'bg-[#18233a]' : ''
                        }`}
                      >
                        <td className="p-3 text-cyan-400 font-bold">{t.approval_id}</td>
                        <td className="p-3 text-slate-300">{t.requester_id}</td>
                        <td className="p-3 text-slate-300">{t.intent}</td>
                        <td className="p-3">
                          <span className={t.policy_risk === 'HIGH' ? 'text-rose-400' : 'text-amber-400'}>
                            {t.policy_risk}
                          </span>
                        </td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              t.status === 'APPROVED'
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                : t.status === 'PENDING'
                                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                : t.status === 'REJECTED'
                                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                : 'bg-slate-700/50 text-slate-400'
                            }`}
                          >
                            {t.status}
                          </span>
                        </td>
                        <td className="p-3 text-right text-slate-400 text-[11px]">Inspect →</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </GlassCard>
        </div>

        {/* Detail & Action Column */}
        <div>
          {selectedTicket ? (
            <GlassCard glow="cyan">
              <div className="space-y-4 font-mono text-xs">
                <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
                  <h3 className="font-bold text-white text-sm">Ticket Details</h3>
                  <span className="text-[10px] text-cyan-400">{selectedTicket.approval_id}</span>
                </div>

                <div className="space-y-2">
                  <div>
                    <span className="text-[10px] text-slate-400 block">Requester User ID</span>
                    <strong className="text-slate-200">{selectedTicket.requester_id}</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Target Resource</span>
                    <strong className="text-slate-200">{selectedTicket.resource}</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Expiration Timestamp</span>
                    <strong className="text-slate-400 text-[11px]">{selectedTicket.expires_at}</strong>
                  </div>
                </div>

                {selectedTicket.status === 'PENDING' && (
                  <div className="pt-3 border-t border-slate-800 space-y-3">
                    <div>
                      <label className="text-[10px] text-slate-400 block mb-1">Approver ID (Must not equal Requester)</label>
                      <input
                        type="text"
                        value={approverId}
                        onChange={(e) => setApproverId(e.target.value)}
                        className="w-full bg-[#0a0f1b] border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none"
                      />
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() =>
                          approveMutation.mutate({ id: selectedTicket.approval_id, approver: approverId })
                        }
                        disabled={approveMutation.isPending}
                        className="flex-1 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center justify-center gap-1 transition-colors disabled:opacity-50"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Approve</span>
                      </button>

                      <button
                        onClick={() =>
                          rejectMutation.mutate({ id: selectedTicket.approval_id, approver: approverId })
                        }
                        disabled={rejectMutation.isPending}
                        className="flex-1 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold flex items-center justify-center gap-1 transition-colors disabled:opacity-50"
                      >
                        <XCircle className="w-4 h-4" />
                        <span>Reject</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </GlassCard>
          ) : (
            <GlassCard>
              <div className="p-8 text-center text-slate-500 font-mono text-xs">
                Select an approval ticket from the table to inspect details and authorize.
              </div>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
};
