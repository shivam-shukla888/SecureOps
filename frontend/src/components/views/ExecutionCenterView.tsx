import React, { useState } from 'react';
import {
  Play,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Cpu,
  Shield,
  Layers,
  FileText,
  Clock,
  Zap,
  Info,
  RotateCcw,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { api, APIError } from '../../services/api';
import { ExecutionResponse } from '../../types/api';
import { useAuth } from '../../context/AuthContext';

export const ExecutionCenterView: React.FC = () => {
  const { tenantId, userRole } = useAuth();

  const [toolName, setToolName] = useState('search_document_tool');
  const [queryInput, setQueryInput] = useState('Corporate Security Architecture');
  const [approvalId, setApprovalId] = useState('');
  const [userId, setUserId] = useState('operator_sarah');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ExecutionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // History of executions performed during the current session
  const [sessionHistory, setSessionHistory] = useState<ExecutionResponse[]>([]);

  const handleExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryInput.trim() || !userId.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let intent = 'SEARCH_DOCUMENT';
      if (toolName === 'read_data_tool') intent = 'READ_DATA';
      else if (toolName === 'update_data_tool') intent = 'UPDATE_DATA';
      else if (toolName === 'delete_data_tool') intent = 'DELETE_DATA';

      const toolInput: Record<string, any> = {
        intent,
        query: queryInput.trim(),
        target_resource: queryInput.trim(),
      };

      const res = await api.executeTool({
        tool_name: toolName,
        tool_input: toolInput,
        user_id: userId.trim(),
        approval_id: approvalId.trim() || undefined,
      });

      setResult(res);
      setSessionHistory((prev) => [res, ...prev.slice(0, 19)]);
    } catch (err: any) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError(err.message || 'Tool execution dispatch failed.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setQueryInput('');
    setApprovalId('');
    setResult(null);
    setError(null);
  };

  const setPreset = (tool: string, query: string, appr: string = '') => {
    setToolName(tool);
    setQueryInput(query);
    setApprovalId(appr);
    setError(null);
  };

  return (
    <div className="space-y-6 select-none">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-white tracking-tight font-mono uppercase">
              EXECUTION CENTER
            </h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              GOVERNED TOOL DISPATCH
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Server-side tool permission execution and timeout-controlled dispatching.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start md:self-auto">
          <div className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-[#111827] border border-slate-800 text-[11px] font-mono text-slate-400">
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

      {/* Main 2-Column Grid: Dispatcher on Left (5 cols), Result/Trace on Right (7 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Governed Tool Dispatcher Form */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-cyan-400" />
                <h2 className="text-sm font-semibold text-white font-mono uppercase">
                  Governed Execution Dispatcher
                </h2>
              </div>
              <span className="text-[10px] text-slate-500 font-mono uppercase">Tool Client</span>
            </div>

            <form onSubmit={handleExecute} className="space-y-4 font-mono text-xs">
              <div>
                <label className="block text-slate-400 mb-1.5 font-medium">
                  User / Agent Identifier
                </label>
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="e.g. operator_sarah"
                  disabled={loading}
                  className="w-full bg-[#0a0f1b] border border-slate-800 focus:border-cyan-500 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none disabled:opacity-50"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1.5 font-medium">
                  Target Governed Tool
                </label>
                <select
                  value={toolName}
                  onChange={(e) => setToolName(e.target.value)}
                  disabled={loading}
                  className="w-full bg-[#0a0f1b] border border-slate-800 focus:border-cyan-500 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none cursor-pointer disabled:opacity-50"
                >
                  <option value="search_document_tool">
                    search_document_tool (Safe Document Search — LOW Risk)
                  </option>
                  <option value="read_data_tool">
                    read_data_tool (Safe Data Retrieval — LOW Risk)
                  </option>
                  <option value="update_data_tool">
                    update_data_tool (Elevated Record Update — Requires Approval)
                  </option>
                  <option value="delete_data_tool">
                    delete_data_tool (Elevated Data Deletion — Requires Approval)
                  </option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1.5 font-medium">
                  Query / Resource Parameter
                </label>
                <input
                  type="text"
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  placeholder="e.g. Corporate Security Architecture or customer_account_502"
                  disabled={loading}
                  className="w-full bg-[#0a0f1b] border border-slate-800 focus:border-cyan-500 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none disabled:opacity-50"
                  required
                />
              </div>

              {(toolName === 'update_data_tool' || toolName === 'delete_data_tool') && (
                <div>
                  <label className="block text-amber-400 mb-1.5 font-medium flex items-center justify-between">
                    <span>HITL Approval Ticket ID</span>
                    <span className="text-[10px] text-slate-500 font-normal">
                      Required for elevated actions
                    </span>
                  </label>
                  <input
                    type="text"
                    value={approvalId}
                    onChange={(e) => setApprovalId(e.target.value)}
                    placeholder="e.g. appr_abc123456789"
                    disabled={loading}
                    className="w-full bg-[#0a0f1b] border border-amber-500/40 focus:border-amber-400 rounded-lg py-2 px-3 text-xs text-amber-200 focus:outline-none disabled:opacity-50"
                  />
                </div>
              )}

              {/* Execution Presets */}
              <div className="pt-1">
                <span className="text-[11px] text-slate-400 block mb-2 font-semibold">
                  Quick Execution Scenarios:
                </span>
                <div className="space-y-1.5">
                  <button
                    type="button"
                    disabled={loading}
                    onClick={() =>
                      setPreset(
                        'search_document_tool',
                        'Corporate Security Architecture'
                      )
                    }
                    className="w-full text-left p-2 rounded-lg bg-[#0e1422] border border-slate-800 hover:border-emerald-500/40 text-[11px] transition-colors flex items-center justify-between group cursor-pointer"
                  >
                    <span className="text-slate-300 group-hover:text-emerald-300">
                      Safe Document Search
                    </span>
                    <span className="text-[10px] text-emerald-400 uppercase">DIRECT DISPATCH</span>
                  </button>

                  <button
                    type="button"
                    disabled={loading}
                    onClick={() =>
                      setPreset('read_data_tool', 'system_audit_metrics')
                    }
                    className="w-full text-left p-2 rounded-lg bg-[#0e1422] border border-slate-800 hover:border-cyan-500/40 text-[11px] transition-colors flex items-center justify-between group cursor-pointer"
                  >
                    <span className="text-slate-300 group-hover:text-cyan-300">
                      Safe Metrics Read
                    </span>
                    <span className="text-[10px] text-cyan-400 uppercase">DIRECT DISPATCH</span>
                  </button>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={handleClear}
                  disabled={loading || (!queryInput && !result && !error)}
                  className="px-3 py-2 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs transition-colors flex items-center gap-1.5 disabled:opacity-40 cursor-pointer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Clear</span>
                </button>

                <button
                  type="submit"
                  disabled={loading || !queryInput.trim()}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center gap-2 transition-colors disabled:opacity-50 cursor-pointer"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Executing Governed Tool...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5" />
                      <span>Execute Tool</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Architectural Distinction Callout */}
          <div className="p-4 rounded-xl bg-[#0e1422] border border-slate-800/80 text-slate-400 text-xs flex items-start gap-2.5">
            <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
            <div className="font-mono text-[11px] leading-relaxed">
              <strong className="text-slate-200 block mb-0.5">
                Authorization ≠ Execution
              </strong>
              Policy evaluates and authorizes intent. Tool execution is an independent governed dispatch step subject to runtime rate limits and approval verification.
            </div>
          </div>
        </div>

        {/* Right Column: Execution Result & Lifecycle */}
        <div className="lg:col-span-7 space-y-4">
          {/* Error Banner */}
          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <strong className="text-xs font-mono font-bold block">
                  Execution Dispatch Error
                </strong>
                <p className="text-xs font-mono">{error}</p>
              </div>
            </div>
          )}

          {/* Idle / Ready State */}
          {!result && !loading && !error && (
            <div className="p-8 rounded-xl bg-[#111827] border border-slate-800/80 text-center space-y-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mx-auto">
                <Play className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white font-mono uppercase">
                  Ready for Governed Execution
                </h3>
                <p className="text-xs text-slate-400 font-mono mt-1 max-w-md mx-auto">
                  Select a tool and specify operational parameters to dispatch execution through the SecureOps tool runtime sandbox.
                </p>
              </div>

              {/* Execution Flow Steps */}
              <div className="pt-4 border-t border-slate-800/80">
                <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block mb-3">
                  Governed Execution Pipeline
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-left font-mono text-[11px]">
                  <div className="p-2 rounded-lg bg-[#0e1422] border border-slate-800 text-slate-400">
                    1. Rate Limit Check
                  </div>
                  <div className="p-2 rounded-lg bg-[#0e1422] border border-slate-800 text-slate-400">
                    2. Approval Verification
                  </div>
                  <div className="p-2 rounded-lg bg-[#0e1422] border border-slate-800 text-slate-400">
                    3. Tool Execution
                  </div>
                  <div className="p-2 rounded-lg bg-[#0e1422] border border-slate-800 text-slate-400">
                    4. Audit Log
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="p-6 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4 font-mono">
              <div className="flex items-center gap-3">
                <RefreshCw className="w-5 h-5 text-emerald-400 animate-spin" />
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    Dispatching Tool Execution...
                  </h3>
                  <p className="text-xs text-slate-400">
                    Validating permissions and executing tool in sandboxed runtime.
                  </p>
                </div>
              </div>

              <div className="space-y-2 pt-3">
                <div className="h-4 bg-slate-800/60 rounded animate-pulse w-3/4" />
                <div className="h-4 bg-slate-800/60 rounded animate-pulse w-1/2" />
              </div>
            </div>
          )}

          {/* Active Result Card */}
          {result && (
            <div className="space-y-4">
              {/* Execution Summary Status */}
              <div
                className={`p-5 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-4 font-mono ${
                  result.status === 'COMPLETED' || result.status === 'executed_post_approval'
                    ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
                    : result.status === 'RUNNING' || result.status === 'QUEUED'
                    ? 'bg-cyan-950/20 border-cyan-500/40 text-cyan-300'
                    : 'bg-rose-950/20 border-rose-500/40 text-rose-300'
                }`}
              >
                <div className="space-y-1">
                  <div className="text-[10px] tracking-wider uppercase text-slate-400">
                    EXECUTION STATUS
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <h2 className="text-xl font-bold tracking-tight uppercase">
                      {result.status}
                    </h2>
                  </div>
                  <p className="text-xs text-slate-300">
                    Governed execution completed in {result.latency_ms.toFixed(1)} ms.
                  </p>
                </div>

                <div className="text-right text-xs shrink-0">
                  <span className="text-slate-400 block text-[10px]">EXECUTION ID</span>
                  <span className="font-bold text-white select-all">{result.execution_id}</span>
                </div>
              </div>

              {/* Execution Details */}
              <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h4 className="text-xs font-semibold text-white uppercase">
                    Execution Telemetry
                  </h4>
                  <span className="text-[10px] text-slate-500">{result.tool_name}</span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 block">REQUEST ID</span>
                    <strong className="text-slate-200 block truncate select-all">
                      {result.request_id}
                    </strong>
                  </div>
                  <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 block">LATENCY</span>
                    <strong className="text-cyan-400 block">
                      {result.latency_ms.toFixed(1)} ms
                    </strong>
                  </div>
                </div>
              </div>

              {/* Result Payload JSON */}
              <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-2 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-cyan-400" />
                    <h4 className="text-xs font-semibold text-white uppercase">
                      Execution Output Payload
                    </h4>
                  </div>
                  <span className="text-[10px] text-slate-500">Real Execution Output</span>
                </div>
                <pre className="p-3 rounded-lg bg-[#0a0f1b] border border-slate-800 text-[11px] text-cyan-300 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(result.result, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Session Execution History (if multiple runs performed) */}
          {sessionHistory.length > 1 && (
            <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h4 className="text-xs font-semibold text-white uppercase">
                  Session Execution Log ({sessionHistory.length})
                </h4>
                <span className="text-[10px] text-slate-500">Recent Dispatches</span>
              </div>

              <div className="space-y-1.5">
                {sessionHistory.map((item, idx) => (
                  <div
                    key={item.execution_id || idx}
                    onClick={() => setResult(item)}
                    className="p-2.5 rounded-lg bg-[#0e1422] border border-slate-800 hover:border-cyan-500/40 cursor-pointer flex items-center justify-between transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-cyan-400 font-bold">{item.tool_name}</span>
                      <span className="text-slate-500 text-[10px] select-all">
                        {item.execution_id}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-slate-400 text-[11px]">
                        {item.latency_ms.toFixed(1)} ms
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                        {item.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
