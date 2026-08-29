import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Filter,
  Search,
  RefreshCw,
  Info,
  Clock,
  ArrowRight,
  Zap,
  RotateCcw,
  FileText,
  Lock,
  Cpu,
} from 'lucide-react';
import { api } from '../../services/api';
import { SecurityEvent } from '../../types/api';
import { useAuth } from '../../context/AuthContext';

export const SecurityEventsView: React.FC = () => {
  const { tenantId, userRole } = useAuth();

  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedEvent, setSelectedEvent] = useState<SecurityEvent | null>(null);

  const {
    data,
    isLoading,
    isError,
    error: fetchError,
    refetch,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ['securityEvents'],
    queryFn: () => api.listSecurityEvents(100),
    refetchInterval: 10000,
  });

  const events: SecurityEvent[] = data?.events || [];

  const filteredEvents = events.filter((e) => {
    const matchesSeverity =
      severityFilter === 'ALL' || e.severity.toUpperCase() === severityFilter.toUpperCase();
    const query = searchTerm.toLowerCase().trim();
    const matchesSearch =
      !query ||
      e.event_type.toLowerCase().includes(query) ||
      (e.request_id && e.request_id.toLowerCase().includes(query)) ||
      (e.user_id && e.user_id.toLowerCase().includes(query)) ||
      JSON.stringify(e.metadata || {}).toLowerCase().includes(query);
    return matchesSeverity && matchesSearch;
  });

  const criticalCount = events.filter(
    (e) => e.severity === 'CRITICAL' || e.severity === 'HIGH'
  ).length;

  const handleResetFilters = () => {
    setSeverityFilter('ALL');
    setSearchTerm('');
  };

  const formattedLastUpdated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString()
    : 'Live';

  return (
    <div className="space-y-4 sm:space-y-6 select-none max-w-full">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 pb-2 border-b border-slate-800/80">
        <div className="min-w-0">
          <div className="flex items-center gap-2 sm:gap-2.5 flex-wrap">
            <h1 className="text-lg sm:text-xl font-bold text-white tracking-tight font-mono uppercase truncate">
              SECURITY EVENTS
            </h1>
            {criticalCount > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-rose-500/10 text-rose-400 border border-rose-500/20 shrink-0">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
                {criticalCount} HIGH RISK
              </span>
            )}
          </div>
          <p className="text-[11px] sm:text-xs text-slate-400 font-mono mt-1">
            Monitor policy violations, blocked activity and security signals across the gateway.
          </p>
        </div>

        <div className="flex items-center gap-2 sm:gap-3 self-start sm:self-auto shrink-0">
          <div className="flex items-center gap-2 sm:gap-3 px-2.5 sm:px-3 py-1.5 rounded-lg bg-[#111827] border border-slate-800 text-[10px] sm:text-[11px] font-mono text-slate-400">
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
            className="px-3 py-2 sm:py-1.5 min-h-[44px] sm:min-h-0 rounded-lg bg-[#111827] border border-slate-800 hover:border-cyan-500/40 text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
            title="Refresh SIEM security events"
            aria-label="Refresh SIEM security events"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filter Controls Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Severity Filter Pills (Horizontally scrollable) */}
        <div className="flex items-center gap-1 p-1 rounded-lg bg-[#111827] border border-slate-800 text-xs font-mono overflow-x-auto max-w-full custom-scrollbar">
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].map((sev) => (
            <button
              key={sev}
              onClick={() => {
                setSeverityFilter(sev);
                setSelectedEvent(null);
              }}
              className={`px-3 py-2 sm:py-1 min-h-[44px] sm:min-h-0 rounded-md transition-colors cursor-pointer whitespace-nowrap flex items-center shrink-0 ${
                severityFilter === sev
                  ? 'bg-slate-800 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        {/* Search & Reset */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search event type, user, ID..."
              className="w-full bg-[#111827] border border-slate-800 focus:border-cyan-500 rounded-lg py-2 sm:py-1.5 pl-8 pr-3 text-xs text-slate-200 font-mono focus:outline-none placeholder:text-slate-600 min-h-[44px] sm:min-h-0"
            />
          </div>

          {(severityFilter !== 'ALL' || searchTerm) && (
            <button
              onClick={handleResetFilters}
              className="px-3 py-2 sm:py-1.5 min-h-[44px] sm:min-h-0 rounded-lg bg-[#111827] border border-slate-800 text-slate-400 hover:text-slate-200 text-xs font-mono flex items-center justify-center gap-1 transition-colors cursor-pointer shrink-0"
              title="Reset active filters"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Grid: Events Feed (7 cols on lg) + Detail Inspection (5 cols on lg) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6 items-start">
        {/* Left Column: Security Events Feed */}
        <div className="lg:col-span-7 space-y-4 w-full">
          <div className="rounded-xl bg-[#111827] border border-slate-800/80 overflow-hidden">
            <div className="p-3.5 sm:p-4 border-b border-slate-800 flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 font-medium">
                {filteredEvents.length} {filteredEvents.length === 1 ? 'Security Event' : 'Security Events'} Logged
              </span>
              <span className="text-[10px] font-mono text-cyan-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                Polling (10s)
              </span>
            </div>

            {isLoading ? (
              <div className="p-8 sm:p-12 text-center text-slate-500 font-mono text-xs space-y-2">
                <RefreshCw className="w-5 h-5 animate-spin mx-auto text-cyan-400" />
                <p>Loading SIEM security event stream...</p>
              </div>
            ) : isError ? (
              <div className="p-6 sm:p-8 text-center text-rose-400 font-mono text-xs space-y-2">
                <AlertTriangle className="w-5 h-5 mx-auto text-rose-400" />
                <p>Failed to load security events. {(fetchError as any)?.message || ''}</p>
                <button
                  onClick={() => refetch()}
                  className="px-3 py-1.5 min-h-[44px] sm:min-h-0 rounded bg-rose-500/20 text-rose-300 text-xs mt-2 cursor-pointer"
                >
                  Retry
                </button>
              </div>
            ) : filteredEvents.length === 0 ? (
              <div className="p-8 sm:p-12 text-center text-slate-500 font-mono text-xs space-y-2">
                <ShieldCheck className="w-8 h-8 mx-auto text-slate-600" />
                <p className="text-slate-300 font-medium">No security events</p>
                <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
                  Security events will appear here when the gateway detects policy violations, prompt injections, or other security signals.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto max-w-full">
                <table className="w-full text-left border-collapse min-w-[500px] sm:min-w-0">
                  <thead>
                    <tr className="border-b border-slate-800 bg-[#0e1422] text-[10px] font-mono uppercase text-slate-400">
                      <th className="p-3">Severity</th>
                      <th className="p-3">Event Type</th>
                      <th className="p-3">User / Request</th>
                      <th className="p-3">Timestamp</th>
                      <th className="p-3 text-right">Inspect</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                    {filteredEvents.map((evt, idx) => {
                      const isSelected =
                        selectedEvent?.event_id === evt.event_id ||
                        (!evt.event_id && selectedEvent === evt);
                      const sev = evt.severity.toUpperCase();
                      return (
                        <tr
                          key={evt.event_id || `evt-${idx}`}
                          onClick={() => setSelectedEvent(evt)}
                          className={`hover:bg-[#151c2e] cursor-pointer transition-colors ${
                            isSelected ? 'bg-[#18233a]' : ''
                          }`}
                        >
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold inline-flex items-center gap-1 shrink-0 ${
                                sev === 'CRITICAL' || sev === 'HIGH'
                                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                  : sev === 'MEDIUM'
                                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                  : sev === 'LOW'
                                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                                  : 'bg-slate-800 text-slate-300 border border-slate-700'
                              }`}
                            >
                              {(sev === 'CRITICAL' || sev === 'HIGH') && (
                                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
                              )}
                              {sev}
                            </span>
                          </td>
                          <td className="p-3">
                            <span className="text-slate-200 font-semibold block break-words">
                              {evt.event_type}
                            </span>
                            {evt.metadata?.reason && (
                              <span className="text-[10px] text-slate-500 truncate max-w-[180px] block">
                                {evt.metadata.reason}
                              </span>
                            )}
                          </td>
                          <td className="p-3">
                            <span className="text-slate-300 block break-all">{evt.user_id || 'System'}</span>
                            <span className="text-[10px] text-slate-500 break-all block">
                              {evt.request_id || evt.event_id || '--'}
                            </span>
                          </td>
                          <td className="p-3 text-[11px] text-slate-400 whitespace-nowrap">
                            {new Date(evt.timestamp).toLocaleTimeString()}
                          </td>
                          <td className="p-3 text-right">
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

        {/* Right Column: Event Detail Inspection */}
        <div className="lg:col-span-5 space-y-4 w-full">
          {selectedEvent ? (
            <div className="p-4 sm:p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4 font-mono text-xs">
              <div className="border-b border-slate-800 pb-3 flex items-center justify-between gap-2 flex-wrap">
                <div>
                  <h3 className="font-bold text-white text-xs sm:text-sm font-mono uppercase">
                    Security Event Detail
                  </h3>
                  <span className="text-[10px] text-cyan-400 break-all">
                    {selectedEvent.event_id || 'Event Log'}
                  </span>
                </div>
                <span
                  className={`px-2.5 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                    selectedEvent.severity === 'CRITICAL' || selectedEvent.severity === 'HIGH'
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      : selectedEvent.severity === 'MEDIUM'
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                  }`}
                >
                  {selectedEvent.severity}
                </span>
              </div>

              {/* Event Context */}
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Event Context
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-2">
                  <div className="flex justify-between gap-2">
                    <span className="text-slate-400">Event Type:</span>
                    <strong className="text-slate-200 text-right break-words">{selectedEvent.event_type}</strong>
                  </div>
                  <div className="flex justify-between gap-2">
                    <span className="text-slate-400">Severity:</span>
                    <strong
                      className={
                        selectedEvent.severity === 'CRITICAL' || selectedEvent.severity === 'HIGH'
                          ? 'text-rose-400'
                          : selectedEvent.severity === 'MEDIUM'
                          ? 'text-amber-400'
                          : 'text-cyan-400'
                      }
                    >
                      {selectedEvent.severity}
                    </strong>
                  </div>
                  <div className="flex justify-between gap-2">
                    <span className="text-slate-400">Timestamp:</span>
                    <span className="text-slate-300 text-[11px] text-right">
                      {new Date(selectedEvent.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Request & Subject Context */}
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Request & Tenant Context
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-2">
                  <div className="flex justify-between gap-2">
                    <span className="text-slate-400">Tenant ID:</span>
                    <strong className="text-slate-200 text-right break-all">{selectedEvent.tenant_id}</strong>
                  </div>
                  {selectedEvent.user_id && (
                    <div className="flex justify-between gap-2">
                      <span className="text-slate-400">User / Agent:</span>
                      <strong className="text-slate-200 text-right break-all">{selectedEvent.user_id}</strong>
                    </div>
                  )}
                  {selectedEvent.request_id && (
                    <div className="flex justify-between gap-2">
                      <span className="text-slate-400">Request ID:</span>
                      <strong className="text-slate-200 select-all text-right break-all">
                        {selectedEvent.request_id}
                      </strong>
                    </div>
                  )}
                </div>
              </div>

              {/* Raw Metadata Payload */}
              <div className="space-y-2 max-w-full overflow-hidden">
                <div className="flex items-center justify-between">
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                    SIEM Metadata Payload
                  </div>
                  <span className="text-[10px] text-slate-500">Real Event Metadata</span>
                </div>
                <pre className="p-3 rounded-lg bg-[#0a0f1b] border border-slate-800 text-[11px] font-mono text-cyan-300 overflow-x-auto whitespace-pre max-w-full">
                  {JSON.stringify(selectedEvent.metadata || {}, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div className="p-6 sm:p-8 rounded-xl bg-[#111827] border border-slate-800/80 text-center space-y-3">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mx-auto">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <h4 className="text-xs font-semibold text-white font-mono uppercase">
                No Event Selected
              </h4>
              <p className="text-[11px] text-slate-400 font-mono max-w-xs mx-auto">
                Select a security event from the SIEM feed on the left to inspect detailed telemetry, affected subjects, and raw metadata.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
