import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, ShieldAlert, Filter, Search, Terminal, Info, Zap } from 'lucide-react';
import { api } from '../../services/api';
import { SecurityEvent } from '../../types/api';
import { GlassCard } from '../layout/GlassCard';

export const SecurityEventsView: React.FC = () => {
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['securityEvents'],
    queryFn: () => api.listSecurityEvents(100),
    refetchInterval: 10000,
  });

  const events: SecurityEvent[] = data?.events || [];

  const filteredEvents = events.filter((e) => {
    const matchesSeverity = severityFilter === 'ALL' || e.severity === severityFilter;
    const matchesSearch =
      !searchTerm ||
      e.event_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      JSON.stringify(e.metadata).toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSeverity && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            SIEM Security Events Console
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Real-time security telemetry monitoring prompt injections, SSRF blocks, and auth violations
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search event type..."
              className="bg-[#141c2e] border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-2 bg-[#141c2e] px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
            <Filter className="w-3.5 h-3.5 text-cyan-400" />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-transparent text-slate-200 font-mono font-semibold focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900">ALL SEVERITIES</option>
              <option value="INFO" className="bg-slate-900">INFO</option>
              <option value="LOW" className="bg-slate-900">LOW</option>
              <option value="MEDIUM" className="bg-slate-900">MEDIUM</option>
              <option value="HIGH" className="bg-slate-900">HIGH</option>
              <option value="CRITICAL" className="bg-slate-900">CRITICAL</option>
            </select>
          </div>
        </div>
      </div>

      {/* Events Table */}
      <GlassCard className="p-0 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400">Captured SIEM Security Events ({filteredEvents.length})</span>
          <button onClick={() => refetch()} className="text-[11px] font-mono text-cyan-400 hover:underline">
            Refresh Telemetry
          </button>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-slate-500 font-mono text-xs">Loading SIEM events...</div>
        ) : filteredEvents.length === 0 ? (
          <div className="p-8 text-center text-slate-500 font-mono text-xs">No matching security events recorded.</div>
        ) : (
          <div className="divide-y divide-slate-800/60 font-mono text-xs">
            {filteredEvents.map((evt, idx) => (
              <div key={evt.event_id || idx} className="p-4 hover:bg-[#161e31] transition-colors space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        evt.severity === 'HIGH' || evt.severity === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : evt.severity === 'MEDIUM'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                      }`}
                    >
                      {evt.severity}
                    </span>
                    <strong className="text-slate-200 text-xs">{evt.event_type}</strong>
                  </div>
                  <span className="text-[11px] text-slate-500">{evt.timestamp}</span>
                </div>

                <div className="p-2.5 rounded-lg bg-[#0a0f1b] border border-slate-800 text-[11px] text-slate-300">
                  <pre className="whitespace-pre-wrap text-cyan-300">
                    {JSON.stringify(evt.metadata, null, 2)}
                  </pre>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  );
};
