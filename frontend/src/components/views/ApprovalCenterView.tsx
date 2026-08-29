import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CheckSquare,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Shield,
  ShieldCheck,
  Search,
  Filter,
  RefreshCw,
  UserCheck,
  FileText,
  Lock,
  Layers,
  ArrowRight,
  ShieldAlert,
  Info,
} from 'lucide-react';
import { api, APIError } from '../../services/api';
import { ApprovalTicket, ApprovalActionResult } from '../../types/api';
import { useAuth } from '../../context/AuthContext';

// Helper hook for live expiry countdown
const useCountdown = (targetIso: string | undefined) => {
  const [timeLeft, setTimeLeft] = useState<{ text: string; isExpired: boolean }>({
    text: '--',
    isExpired: false,
  });

  useEffect(() => {
    if (!targetIso) return;

    const calculate = () => {
      const diff = new Date(targetIso).getTime() - Date.now();
      if (diff <= 0) {
        setTimeLeft({ text: 'EXPIRED', isExpired: true });
        return;
      }

      const totalSeconds = Math.floor(diff / 1000);
      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;

      if (hours > 0) {
        setTimeLeft({ text: `${hours}h ${minutes}m`, isExpired: false });
      } else {
        setTimeLeft({ text: `${minutes}m ${seconds}s`, isExpired: false });
      }
    };

    calculate();
    const interval = setInterval(calculate, 1000);
    return () => clearInterval(interval);
  }, [targetIso]);

  return timeLeft;
};

export const ApprovalCenterView: React.FC = () => {
  const queryClient = useQueryClient();
  const { tenantId, userRole } = useAuth();

  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedTicket, setSelectedTicket] = useState<ApprovalTicket | null>(null);
  const [approverId, setApproverId] = useState<string>('security_officer_bob');
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<ApprovalActionResult | null>(null);

  const canAuthorize = userRole === 'OWNER' || userRole === 'ADMIN' || userRole === 'APPROVER';

  const {
    data,
    isLoading,
    isError,
    error: fetchError,
    refetch,
  } = useQuery({
    queryKey: ['approvals', statusFilter],
    queryFn: () => api.listApprovals(statusFilter === 'ALL' ? undefined : statusFilter),
    refetchInterval: 8000,
  });

  const approveMutation = useMutation({
    mutationFn: ({ id, approver }: { id: string; approver: string }) =>
      api.approveRequest(id, approver),
    onSuccess: (res) => {
      setActionError(null);
      setActionSuccess(res);
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
      if (selectedTicket && selectedTicket.approval_id === res.approval_id) {
        setSelectedTicket({
          ...selectedTicket,
          status: 'APPROVED',
          approver_id: res.approver_id,
        });
      }
    },
    onError: (err: any) => {
      setActionSuccess(null);
      setActionError(err.message || 'Failed to authorize approval ticket.');
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, approver }: { id: string; approver: string }) =>
      api.rejectRequest(id, approver),
    onSuccess: (res) => {
      setActionError(null);
      setActionSuccess(res);
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
      if (selectedTicket && selectedTicket.approval_id === res.approval_id) {
        setSelectedTicket({
          ...selectedTicket,
          status: 'REJECTED',
          approver_id: res.approver_id,
        });
      }
    },
    onError: (err: any) => {
      setActionSuccess(null);
      setActionError(err.message || 'Failed to reject approval ticket.');
    },
  });

  const tickets = data?.approvals || [];

  const filteredTickets = tickets.filter((t) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      t.approval_id.toLowerCase().includes(query) ||
      t.request_id.toLowerCase().includes(query) ||
      t.requester_id.toLowerCase().includes(query) ||
      t.intent.toLowerCase().includes(query) ||
      t.resource.toLowerCase().includes(query)
    );
  });

  const pendingCount = tickets.filter((t) => t.status === 'PENDING').length;
  const selectedCountdown = useCountdown(selectedTicket?.expires_at);

  return (
    <div className="space-y-4 sm:space-y-6 select-none max-w-full">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 pb-2 border-b border-slate-800/80">
        <div className="min-w-0">
          <div className="flex items-center gap-2 sm:gap-2.5 flex-wrap">
            <h1 className="text-lg sm:text-xl font-bold text-white tracking-tight font-mono uppercase truncate">
              APPROVAL CENTER
            </h1>
            {pendingCount > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                {pendingCount} PENDING
              </span>
            )}
          </div>
          <p className="text-[11px] sm:text-xs text-slate-400 font-mono mt-1">
            Review and authorize elevated-risk actions before execution.
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

          <button
            onClick={() => refetch()}
            className="px-3 py-2 sm:py-1.5 min-h-[44px] sm:min-h-0 rounded-lg bg-[#111827] border border-slate-800 hover:border-cyan-500/40 text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
            title="Refresh approval queue"
            aria-label="Refresh approval queue"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* RBAC Notice if user cannot approve */}
      {!canAuthorize && (
        <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-mono flex items-center gap-2.5">
          <Info className="w-4 h-4 text-amber-400 shrink-0" />
          <span className="break-words">
            Current role <strong className="uppercase">{userRole}</strong> has read-only access. Only <strong>OWNER</strong>, <strong>ADMIN</strong>, or <strong>APPROVER</strong> roles may authorize tickets.
          </span>
        </div>
      )}

      {/* Action Error / Success Banners */}
      {actionError && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-mono flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span className="break-words">{actionError}</span>
          </div>
          <button
            onClick={() => setActionError(null)}
            className="text-slate-400 hover:text-white text-xs px-2 min-h-[44px] flex items-center"
            aria-label="Dismiss error"
          >
            ✕
          </button>
        </div>
      )}

      {actionSuccess && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="break-words">{actionSuccess.message}</span>
          </div>
          <button
            onClick={() => setActionSuccess(null)}
            className="text-slate-400 hover:text-white text-xs px-2 min-h-[44px] flex items-center"
            aria-label="Dismiss message"
          >
            ✕
          </button>
        </div>
      )}

      {/* Filter Tabs & Search Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Status Filter Pills (Horizontally scrollable on mobile) */}
        <div className="flex items-center gap-1.5 p-1 rounded-lg bg-[#111827] border border-slate-800 text-xs font-mono overflow-x-auto max-w-full custom-scrollbar">
          {['ALL', 'PENDING', 'APPROVED', 'REJECTED', 'EXPIRED'].map((status) => (
            <button
              key={status}
              onClick={() => {
                setStatusFilter(status);
                setSelectedTicket(null);
              }}
              className={`px-3 py-2 sm:py-1 min-h-[44px] sm:min-h-0 rounded-md transition-colors whitespace-nowrap cursor-pointer flex items-center shrink-0 ${
                statusFilter === status
                  ? 'bg-slate-800 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              {status}
              {status === 'PENDING' && pendingCount > 0 && (
                <span className="ml-1.5 px-1 py-0.2 rounded bg-amber-500/20 text-amber-300 text-[10px]">
                  {pendingCount}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tickets, users, intent..."
            className="w-full bg-[#111827] border border-slate-800 focus:border-cyan-500 rounded-lg py-2 sm:py-1.5 pl-8 pr-3 text-xs text-slate-200 font-mono focus:outline-none placeholder:text-slate-600 min-h-[44px] sm:min-h-0"
          />
        </div>
      </div>

      {/* Main Grid: Queue on Left (7 cols on lg), Detail on Right (5 cols on lg) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6 items-start">
        {/* Left Column: Approval Queue */}
        <div className="lg:col-span-7 space-y-4 w-full">
          <div className="rounded-xl bg-[#111827] border border-slate-800/80 overflow-hidden">
            <div className="p-3.5 sm:p-4 border-b border-slate-800 flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 font-medium">
                {filteredTickets.length} {filteredTickets.length === 1 ? 'Ticket' : 'Tickets'} Listed
              </span>
              <span className="text-[10px] font-mono text-cyan-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                Live Polling (8s)
              </span>
            </div>

            {isLoading ? (
              <div className="p-8 sm:p-12 text-center text-slate-500 font-mono text-xs space-y-2">
                <RefreshCw className="w-5 h-5 animate-spin mx-auto text-cyan-400" />
                <p>Loading security approval queue...</p>
              </div>
            ) : isError ? (
              <div className="p-6 sm:p-8 text-center text-rose-400 font-mono text-xs space-y-2">
                <AlertTriangle className="w-5 h-5 mx-auto text-rose-400" />
                <p>Failed to load approval tickets. {(fetchError as any)?.message || ''}</p>
                <button
                  onClick={() => refetch()}
                  className="px-3 py-1.5 min-h-[44px] sm:min-h-0 rounded bg-rose-500/20 text-rose-300 text-xs mt-2 cursor-pointer"
                >
                  Retry
                </button>
              </div>
            ) : filteredTickets.length === 0 ? (
              <div className="p-8 sm:p-12 text-center text-slate-500 font-mono text-xs space-y-2">
                <ShieldCheck className="w-8 h-8 mx-auto text-slate-600" />
                <p className="text-slate-300 font-medium">No approval tickets found</p>
                <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
                  Elevated-risk operations requiring Human-in-the-Loop authorization will appear in this queue.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto max-w-full">
                <table className="w-full text-left border-collapse min-w-[540px] sm:min-w-0">
                  <thead>
                    <tr className="border-b border-slate-800 bg-[#0e1422] text-[10px] font-mono uppercase text-slate-400">
                      <th className="p-3">Ticket ID</th>
                      <th className="p-3">Requester</th>
                      <th className="p-3">Intent</th>
                      <th className="p-3">Risk</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                    {filteredTickets.map((t) => {
                      const isSelected = selectedTicket?.approval_id === t.approval_id;
                      return (
                        <tr
                          key={t.approval_id}
                          onClick={() => {
                            setSelectedTicket(t);
                            setActionError(null);
                            setActionSuccess(null);
                          }}
                          className={`hover:bg-[#151c2e] cursor-pointer transition-colors ${
                            isSelected ? 'bg-[#18233a]' : ''
                          }`}
                        >
                          <td className="p-3">
                            <span className="text-cyan-400 font-bold block break-all">{t.approval_id}</span>
                            <span className="text-[10px] text-slate-500 break-all">{t.request_id}</span>
                          </td>
                          <td className="p-3 text-slate-300 break-all">{t.requester_id}</td>
                          <td className="p-3">
                            <span className="text-slate-200 block break-words">{t.intent}</span>
                            <span className="text-[10px] text-slate-500 truncate max-w-[120px] block">
                              {t.resource}
                            </span>
                          </td>
                          <td className="p-3">
                            <span
                              className={`text-[10px] font-bold ${
                                t.policy_risk === 'HIGH'
                                  ? 'text-rose-400'
                                  : t.policy_risk === 'MEDIUM'
                                  ? 'text-amber-400'
                                  : 'text-emerald-400'
                              }`}
                            >
                              {t.policy_risk}
                            </span>
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold inline-flex items-center gap-1 shrink-0 ${
                                t.status === 'APPROVED'
                                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                  : t.status === 'PENDING'
                                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                  : t.status === 'REJECTED'
                                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                  : 'bg-slate-800 text-slate-400 border border-slate-700'
                              }`}
                            >
                              {t.status === 'PENDING' && (
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                              )}
                              {t.status}
                            </span>
                          </td>
                          <td className="p-3 text-right text-slate-400 text-[11px]">
                            <ArrowRight className="w-3.5 h-3.5 inline text-slate-500" />
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

        {/* Right Column: Approval Ticket Details & Authorization Actions */}
        <div className="lg:col-span-5 space-y-4 w-full">
          {selectedTicket ? (
            <div className="p-4 sm:p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4">
              <div className="border-b border-slate-800 pb-3 flex items-center justify-between gap-2 flex-wrap">
                <div>
                  <h3 className="font-bold text-white text-xs sm:text-sm font-mono uppercase">
                    Ticket Authorization
                  </h3>
                  <span className="text-[10px] font-mono text-cyan-400 break-all">
                    {selectedTicket.approval_id}
                  </span>
                </div>
                <span
                  className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold shrink-0 ${
                    selectedTicket.status === 'APPROVED'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : selectedTicket.status === 'PENDING'
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : selectedTicket.status === 'REJECTED'
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}
                >
                  {selectedTicket.status}
                </span>
              </div>

              {/* Request Context */}
              <div className="space-y-2 font-mono text-xs">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Request Context
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-2">
                  <div className="flex justify-between gap-2">
                    <span className="text-slate-400">Request ID:</span>
                    <strong className="text-slate-200 select-all text-right break-all">{selectedTicket.request_id}</strong>
                  </div>
                  <div className="flex justify-between gap-2">
                    <span className="text-slate-400">Requester User:</span>
                    <strong className="text-slate-200 text-right break-all">{selectedTicket.requester_id}</strong>
                  </div>
                  <div className="flex justify-between gap-2">
                    <span className="text-slate-400">Classified Intent:</span>
                    <strong className="text-slate-200 text-right break-words">{selectedTicket.intent}</strong>
                  </div>
                  <div className="flex justify-between gap-2">
                    <span className="text-slate-400">Target Resource:</span>
                    <strong className="text-slate-200 text-right break-words">{selectedTicket.resource}</strong>
                  </div>
                  <div className="flex justify-between gap-2">
                    <span className="text-slate-400">Created At:</span>
                    <span className="text-slate-400 text-[11px] text-right">
                      {new Date(selectedTicket.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Security & Expiry Context */}
              <div className="space-y-2 font-mono text-xs">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Security & Expiry Context
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Policy Risk Level:</span>
                    <strong
                      className={
                        selectedTicket.policy_risk === 'HIGH'
                          ? 'text-rose-400'
                          : selectedTicket.policy_risk === 'MEDIUM'
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }
                    >
                      {selectedTicket.policy_risk}
                    </strong>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Expiration Window:</span>
                    <span
                      className={`text-xs font-bold font-mono px-2 py-0.5 rounded ${
                        selectedCountdown.isExpired
                          ? 'bg-rose-500/20 text-rose-400'
                          : 'bg-amber-500/20 text-amber-300'
                      }`}
                    >
                      <Clock className="w-3 h-3 inline mr-1" />
                      {selectedCountdown.text}
                    </span>
                  </div>
                  {selectedTicket.approver_id && (
                    <div className="flex justify-between pt-1 border-t border-slate-800 gap-2">
                      <span className="text-slate-400">Decided By:</span>
                      <strong className="text-cyan-400 text-right break-all">{selectedTicket.approver_id}</strong>
                    </div>
                  )}
                </div>
              </div>

              {/* Status Message */}
              <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 font-mono text-[11px] text-slate-400">
                {selectedTicket.status === 'PENDING' && (
                  <div className="flex items-center gap-2 text-amber-300">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    <span>Human authorization is required before tool execution can proceed.</span>
                  </div>
                )}
                {selectedTicket.status === 'APPROVED' && (
                  <div className="flex items-center gap-2 text-emerald-400">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>Approved — execution authorized by security officer.</span>
                  </div>
                )}
                {selectedTicket.status === 'REJECTED' && (
                  <div className="flex items-center gap-2 text-rose-400">
                    <XCircle className="w-4 h-4 shrink-0" />
                    <span>Rejected — execution is prohibited.</span>
                  </div>
                )}
                {selectedTicket.status === 'EXPIRED' && (
                  <div className="flex items-center gap-2 text-slate-400">
                    <Clock className="w-4 h-4 shrink-0" />
                    <span>Ticket expired — authorization window elapsed.</span>
                  </div>
                )}
              </div>

              {/* Action Controls for PENDING tickets */}
              {selectedTicket.status === 'PENDING' && (
                <div className="pt-3 border-t border-slate-800 space-y-3 font-mono text-xs">
                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1">
                      Approver Security ID (Must not match Requester)
                    </label>
                    <input
                      type="text"
                      value={approverId}
                      onChange={(e) => setApproverId(e.target.value)}
                      disabled={!canAuthorize || approveMutation.isPending || rejectMutation.isPending}
                      className="w-full bg-[#0a0f1b] border border-slate-800 focus:border-cyan-500 rounded-lg px-3 py-2.5 sm:py-2 text-xs text-slate-200 focus:outline-none disabled:opacity-50 min-h-[44px] sm:min-h-0"
                      placeholder="e.g. security_officer_bob"
                    />
                  </div>

                  <div className="flex flex-col sm:flex-row gap-2.5 sm:gap-3">
                    <button
                      onClick={() =>
                        approveMutation.mutate({
                          id: selectedTicket.approval_id,
                          approver: approverId.trim(),
                        })
                      }
                      disabled={
                        !canAuthorize ||
                        !approverId.trim() ||
                        approveMutation.isPending ||
                        rejectMutation.isPending ||
                        selectedCountdown.isExpired
                      }
                      className="flex-1 py-3 sm:py-2.5 min-h-[44px] rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50 cursor-pointer"
                    >
                      {approveMutation.isPending ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <CheckCircle2 className="w-4 h-4" />
                      )}
                      <span>Authorize (Approve)</span>
                    </button>

                    <button
                      onClick={() =>
                        rejectMutation.mutate({
                          id: selectedTicket.approval_id,
                          approver: approverId.trim(),
                        })
                      }
                      disabled={
                        !canAuthorize ||
                        !approverId.trim() ||
                        approveMutation.isPending ||
                        rejectMutation.isPending
                      }
                      className="flex-1 py-3 sm:py-2.5 min-h-[44px] rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50 cursor-pointer"
                    >
                      {rejectMutation.isPending ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <XCircle className="w-4 h-4" />
                      )}
                      <span>Deny (Reject)</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-6 sm:p-8 rounded-xl bg-[#111827] border border-slate-800/80 text-center space-y-3">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mx-auto">
                <CheckSquare className="w-5 h-5" />
              </div>
              <h4 className="text-xs font-semibold text-white font-mono uppercase">
                No Ticket Selected
              </h4>
              <p className="text-[11px] text-slate-400 font-mono max-w-xs mx-auto">
                Select an approval ticket from the queue on the left to inspect request metadata, review security context, and authorize or deny execution.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
