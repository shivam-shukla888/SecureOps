import React, { useState } from 'react';
import { Play, CheckCircle2, AlertTriangle, RefreshCw, Terminal, Wrench } from 'lucide-react';
import { api } from '../../services/api';
import { ExecutionResponse } from '../../types/api';
import { GlassCard } from '../layout/GlassCard';

export const ExecutionCenterView: React.FC = () => {
  const [toolName, setToolName] = useState('search_document_tool');
  const [queryInput, setQueryInput] = useState('Corporate Security Policy');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ExecutionResponse | null>(null);
  const [error, setError] = useState('');

  const handleExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const toolInput: Record<string, any> = toolName === 'search_document_tool' 
        ? { intent: 'SEARCH_DOCUMENT', query: queryInput }
        : { intent: 'READ_DATA', target_resource: queryInput || 'system_logs' };

      const res = await api.executeTool({
        tool_name: toolName,
        tool_input: toolInput,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Tool execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          Execution Center
          <Play className="w-5 h-5 text-emerald-400" />
        </h1>
        <p className="text-xs text-slate-400 font-mono mt-0.5">
          Server-side tool permission execution and timeout-controlled dispatching
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <GlassCard>
            <form onSubmit={handleExecute} className="space-y-4 font-mono text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Select Tool</label>
                <select
                  value={toolName}
                  onChange={(e) => setToolName(e.target.value)}
                  className="w-full bg-[#0a0f1b] border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none"
                >
                  <option value="search_document_tool">search_document_tool (Safe Read-Only Document Search)</option>
                  <option value="read_data_tool">read_data_tool (Safe Data Retrieval)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Search Query Parameter</label>
                <input
                  type="text"
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  className="w-full bg-[#0a0f1b] border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none"
                />
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center gap-2 transition-colors disabled:opacity-50"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  <span>Execute Tool</span>
                </button>
              </div>
            </form>
          </GlassCard>

          {result && (
            <GlassCard glow="emerald">
              <div className="space-y-3 font-mono text-xs">
                <div className="border-b border-slate-800 pb-2 flex items-center justify-between">
                  <h3 className="font-bold text-emerald-400">Execution Succeeded</h3>
                  <span className="text-slate-400">{result.latency_ms.toFixed(1)} ms</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block">Execution ID</span>
                  <strong className="text-slate-200">{result.execution_id}</strong>
                </div>
                <pre className="p-3 rounded-lg bg-[#0a0f1b] border border-slate-800 whitespace-pre-wrap text-[11px] text-cyan-300">
                  {JSON.stringify(result.result, null, 2)}
                </pre>
              </div>
            </GlassCard>
          )}

          {error && (
            <GlassCard glow="rose">
              <div className="text-xs text-rose-400 flex items-center gap-2 font-mono">
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
