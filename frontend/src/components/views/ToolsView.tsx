import React from 'react';
import { Wrench, ShieldCheck, Lock, CheckCircle2 } from 'lucide-react';
import { GlassCard } from '../layout/GlassCard';

export const ToolsView: React.FC = () => {
  const tools = [
    { name: 'search_document_tool', intent: 'SEARCH_DOCUMENT', risk: 'LOW', approval: false, desc: 'Safe read-only document search via DocumentServiceAdapter.' },
    { name: 'read_data_tool', intent: 'READ_DATA', risk: 'LOW', approval: false, desc: 'Read-only dataset search with strict tenant scoping.' },
    { name: 'update_data_tool', intent: 'UPDATE_DATA', risk: 'MEDIUM', approval: true, desc: 'Data modification tool requiring HITL approval authorization.' },
    { name: 'delete_data_tool', intent: 'DELETE_DATA', risk: 'HIGH', approval: true, desc: 'Destructive table deletion tool requiring high-risk HITL approval.' },
    { name: 'send_document_tool', intent: 'SEND_DOCUMENT', risk: 'HIGH', approval: true, desc: 'Document exfiltration/dispatch tool requiring approval.' },
  ];

  return (
    <div className="space-y-6 font-mono">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          Tools & Permissions Registry
          <Wrench className="w-5 h-5 text-cyan-400" />
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Server-side tool allowlist mapping intents to permission controls
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tools.map((t) => (
          <GlassCard key={t.name}>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <strong className="text-cyan-400 font-bold">{t.name}</strong>
                <span className={`px-2 py-0.5 rounded text-[10px] ${t.approval ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                  {t.approval ? 'REQUIRES APPROVAL' : 'SAFE ALLOW'}
                </span>
              </div>
              <p className="text-slate-400 text-[11px] font-sans">{t.desc}</p>
              <div className="pt-2 text-[10px] text-slate-500 flex justify-between">
                <span>Intent: <strong className="text-slate-300">{t.intent}</strong></span>
                <span>Risk: <strong className={t.risk === 'HIGH' ? 'text-rose-400' : 'text-slate-300'}>{t.risk}</strong></span>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  );
};
