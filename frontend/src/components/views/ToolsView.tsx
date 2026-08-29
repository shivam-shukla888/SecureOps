import React, { useState } from 'react';
import {
  Wrench,
  Shield,
  ShieldCheck,
  ShieldAlert,
  Search,
  Filter,
  RotateCcw,
  CheckCircle2,
  Clock,
  Lock,
  ArrowRight,
  Info,
  Layers,
  Cpu,
  FileText,
  AlertTriangle,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export interface GovernedTool {
  id: string;
  name: string;
  intent: string;
  risk: 'LOW' | 'MEDIUM' | 'HIGH';
  requires_approval: boolean;
  category: 'READ' | 'WRITE' | 'DESTRUCTIVE' | 'COMMUNICATION';
  description: string;
  parameters: {
    name: string;
    type: string;
    required: boolean;
    description: string;
    constraints?: string;
  }[];
  security_controls: string[];
}

export const GOVERNED_TOOLS: GovernedTool[] = [
  {
    id: 'tool_search_doc',
    name: 'search_document',
    intent: 'SEARCH_DOCUMENT',
    risk: 'LOW',
    requires_approval: false,
    category: 'READ',
    description: 'Safely searches indexed tenant documentation via DocumentServiceAdapter.',
    parameters: [
      {
        name: 'query',
        type: 'string',
        required: true,
        description: 'Search terms to query in document indexes.',
        constraints: 'Min length: 1, Max length: 4096, Traversal & Injection Sanitized',
      },
      {
        name: 'document_id',
        type: 'string',
        required: false,
        description: 'Specific document identifier to scope search.',
        constraints: 'Optional string identifier',
      },
    ],
    security_controls: [
      'Strict Tenant Scoping',
      'Path Traversal Regex Sanitization',
      'Command Injection Sanitization',
      'Safe Direct Execution',
    ],
  },
  {
    id: 'tool_read_data',
    name: 'read_data',
    intent: 'READ_DATA',
    risk: 'LOW',
    requires_approval: false,
    category: 'READ',
    description: 'Reads non-sensitive database records with strict tenant scoping.',
    parameters: [
      {
        name: 'target_resource',
        type: 'string',
        required: true,
        description: 'Target data collection or table resource.',
        constraints: 'Min length: 1, Forbidden special characters',
      },
      {
        name: 'limit',
        type: 'integer',
        required: false,
        description: 'Maximum number of records to return.',
        constraints: 'Min: 1, Max: 1000, Default: 100',
      },
    ],
    security_controls: [
      'Tenant Boundary Isolation',
      'Query Pagination Limit Enforcement',
      'Direct Safe Execution',
    ],
  },
  {
    id: 'tool_update_data',
    name: 'update_data',
    intent: 'UPDATE_DATA',
    risk: 'MEDIUM',
    requires_approval: true,
    category: 'WRITE',
    description: 'Updates existing tenant records. Requires Human-in-the-Loop authorization.',
    parameters: [
      {
        name: 'target_resource',
        type: 'string',
        required: true,
        description: 'Target database record or collection identifier.',
        constraints: 'Min length: 1, Sanitized against traversal',
      },
      {
        name: 'update_fields',
        type: 'object (key-value)',
        required: true,
        description: 'Dictionary of field updates to apply to the target resource.',
        constraints: 'Key-value strings, sanitized input validation',
      },
    ],
    security_controls: [
      'HITL Approval Ticket Required',
      'Target Resource Binding Verification',
      'Separation of Duties (Approver ≠ Requester)',
      'Time-Bound Expiration Verification',
    ],
  },
  {
    id: 'tool_send_doc',
    name: 'send_document',
    intent: 'SEND_DOCUMENT',
    risk: 'HIGH',
    requires_approval: true,
    category: 'COMMUNICATION',
    description: 'Transmits documents externally with SSRF protection and destination validation.',
    parameters: [
      {
        name: 'document_id',
        type: 'string',
        required: true,
        description: 'Identifier of the document to transmit.',
        constraints: 'Min length: 1, Sanitized string',
      },
      {
        name: 'recipient_email',
        type: 'string',
        required: true,
        description: 'Destination email address for outbound dispatch.',
        constraints: 'Valid email address format',
      },
      {
        name: 'destination_host',
        type: 'string',
        required: true,
        description: 'Target host domain or IP for dispatch routing.',
        constraints: 'SSRFProtector domain whitelist validation (private IPs blocked)',
      },
    ],
    security_controls: [
      'HITL Approval Ticket Required',
      'SSRF Protection (Private IP & Loopback Blocked)',
      'Outbound Destination Whitelisting',
      'SHA-256 Audit Commitment',
    ],
  },
  {
    id: 'tool_delete_data',
    name: 'delete_data',
    intent: 'DELETE_DATA',
    risk: 'HIGH',
    requires_approval: true,
    category: 'DESTRUCTIVE',
    description: 'Purges or deletes data records. Requires elevated security authorization.',
    parameters: [
      {
        name: 'target_resource',
        type: 'string',
        required: true,
        description: 'Target resource to permanently delete.',
        constraints: 'Min length: 1, Sanitized string',
      },
      {
        name: 'confirm_token',
        type: 'string',
        required: true,
        description: 'Explicit confirmation token required for destructive operation.',
        constraints: 'Non-empty verification token',
      },
    ],
    security_controls: [
      'HITL Approval Ticket Required',
      'Explicit Confirmation Token Gate',
      'Anti-Downgrade Policy Enforcement',
      'Immutable SHA-256 Audit Trail',
    ],
  },
];

export const ToolsView: React.FC = () => {
  const { tenantId, userRole } = useAuth();

  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [approvalFilter, setApprovalFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedTool, setSelectedTool] = useState<GovernedTool | null>(GOVERNED_TOOLS[0]);

  const filteredTools = GOVERNED_TOOLS.filter((t) => {
    const matchesRisk = riskFilter === 'ALL' || t.risk === riskFilter;
    const matchesApproval =
      approvalFilter === 'ALL' ||
      (approvalFilter === 'APPROVAL_REQUIRED' && t.requires_approval) ||
      (approvalFilter === 'SAFE_ALLOW' && !t.requires_approval);
    const query = searchTerm.toLowerCase().trim();
    const matchesSearch =
      !query ||
      t.name.toLowerCase().includes(query) ||
      t.intent.toLowerCase().includes(query) ||
      t.description.toLowerCase().includes(query) ||
      t.parameters.some((p) => p.name.toLowerCase().includes(query));
    return matchesRisk && matchesApproval && matchesSearch;
  });

  const handleResetFilters = () => {
    setRiskFilter('ALL');
    setApprovalFilter('ALL');
    setSearchTerm('');
  };

  return (
    <div className="space-y-6 select-none">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-white tracking-tight font-mono uppercase">
              TOOL GOVERNANCE
            </h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              5 GOVERNED TOOLS
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Manage and inspect the tools available to governed AI agents.
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

      {/* Filter Controls Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Risk & Approval Filter Pills */}
        <div className="flex flex-wrap items-center gap-1 p-1 rounded-lg bg-[#111827] border border-slate-800 text-xs font-mono">
          {['ALL', 'LOW', 'MEDIUM', 'HIGH'].map((risk) => (
            <button
              key={risk}
              onClick={() => setRiskFilter(risk)}
              className={`px-3 py-1 rounded-md transition-colors cursor-pointer ${
                riskFilter === risk
                  ? 'bg-slate-800 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              {risk === 'ALL' ? 'ALL RISKS' : `${risk} RISK`}
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
              placeholder="Search tool, intent, parameter..."
              className="w-full bg-[#111827] border border-slate-800 focus:border-cyan-500 rounded-lg py-1.5 pl-8 pr-3 text-xs text-slate-200 font-mono focus:outline-none placeholder:text-slate-600"
            />
          </div>

          {(riskFilter !== 'ALL' || approvalFilter !== 'ALL' || searchTerm) && (
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

      {/* Main Grid: Tool Inventory Table (7 cols) + Detail Inspector (5 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Governed Tool Inventory */}
        <div className="lg:col-span-7 space-y-4">
          <div className="rounded-xl bg-[#111827] border border-slate-800/80 overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 font-medium">
                {filteredTools.length} Governed {filteredTools.length === 1 ? 'Tool' : 'Tools'}{' '}
                Registered
              </span>
              <span className="text-[10px] font-mono text-cyan-400 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                Deterministic Registry
              </span>
            </div>

            {filteredTools.length === 0 ? (
              <div className="p-12 text-center text-slate-500 font-mono text-xs space-y-2">
                <Wrench className="w-8 h-8 mx-auto text-slate-600" />
                <p className="text-slate-300 font-medium">No matching tools found</p>
                <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
                  Adjust your search or risk filters to view registered governed tools.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-[#0e1422] text-[10px] font-mono uppercase text-slate-400">
                      <th className="p-3">Tool Name</th>
                      <th className="p-3">Intent Mapping</th>
                      <th className="p-3">Risk</th>
                      <th className="p-3">Governance Gate</th>
                      <th className="p-3 text-right">Inspect</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                    {filteredTools.map((tool) => {
                      const isSelected = selectedTool?.name === tool.name;
                      return (
                        <tr
                          key={tool.name}
                          onClick={() => setSelectedTool(tool)}
                          className={`hover:bg-[#151c2e] cursor-pointer transition-colors ${
                            isSelected ? 'bg-[#18233a]' : ''
                          }`}
                        >
                          <td className="p-3">
                            <span className="text-cyan-400 font-bold block">{tool.name}</span>
                            <span className="text-[10px] text-slate-500 truncate max-w-[160px] block">
                              {tool.description}
                            </span>
                          </td>
                          <td className="p-3 text-slate-300">{tool.intent}</td>
                          <td className="p-3">
                            <span
                              className={`text-[10px] font-bold ${
                                tool.risk === 'HIGH'
                                  ? 'text-rose-400'
                                  : tool.risk === 'MEDIUM'
                                  ? 'text-amber-400'
                                  : 'text-emerald-400'
                              }`}
                            >
                              {tool.risk}
                            </span>
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold inline-flex items-center gap-1 ${
                                tool.requires_approval
                                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                  : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                              }`}
                            >
                              {tool.requires_approval ? 'REQUIRES APPROVAL' : 'SAFE ALLOW'}
                            </span>
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

          {/* Architecture Explanation Callout */}
          <div className="p-4 rounded-xl bg-[#0e1422] border border-slate-800/80 text-slate-400 text-xs flex items-start gap-2.5 font-mono">
            <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
            <div className="text-[11px] leading-relaxed">
              <strong className="text-slate-200 block mb-0.5">
                Tool Governance & Policy Enforcement
              </strong>
              Tool governance defines the capabilities available to AI agents. Intent is evaluated by the deterministic policy engine before any tool execution occurs.
            </div>
          </div>
        </div>

        {/* Right Column: Tool Detail Inspector */}
        <div className="lg:col-span-5 space-y-4">
          {selectedTool ? (
            <div className="p-5 rounded-xl bg-[#111827] border border-slate-800/80 space-y-4 font-mono text-xs">
              <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-white text-sm font-mono uppercase">
                    Tool Specification
                  </h3>
                  <span className="text-[10px] text-cyan-400 font-bold">{selectedTool.name}</span>
                </div>
                <span
                  className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                    selectedTool.requires_approval
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  }`}
                >
                  {selectedTool.requires_approval ? 'APPROVAL REQUIRED' : 'DIRECT ALLOW'}
                </span>
              </div>

              {/* Tool Identity */}
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Identity & Intent
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Tool Name:</span>
                    <strong className="text-slate-200">{selectedTool.name}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Bound Intent:</span>
                    <strong className="text-slate-200">{selectedTool.intent}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Category:</span>
                    <strong className="text-cyan-300">{selectedTool.category}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Minimum Risk:</span>
                    <strong
                      className={
                        selectedTool.risk === 'HIGH'
                          ? 'text-rose-400'
                          : selectedTool.risk === 'MEDIUM'
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }
                    >
                      {selectedTool.risk}
                    </strong>
                  </div>
                  <div className="pt-1 border-t border-slate-800 text-[11px] text-slate-300">
                    {selectedTool.description}
                  </div>
                </div>
              </div>

              {/* Parameter Schema */}
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Parameter Validation Schema ({selectedTool.parameters.length})
                </div>
                <div className="space-y-2">
                  {selectedTool.parameters.map((param) => (
                    <div
                      key={param.name}
                      className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-cyan-300 font-bold">{param.name}</span>
                        <span
                          className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                            param.required
                              ? 'bg-rose-500/20 text-rose-300'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {param.required ? 'REQUIRED' : 'OPTIONAL'}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400">{param.description}</div>
                      <div className="text-[10px] text-slate-500">
                        Type: <span className="text-slate-300">{param.type}</span>
                        {param.constraints && (
                          <span className="block text-slate-500 mt-0.5">
                            Constraints: {param.constraints}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Security Controls */}
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Active Security Controls
                </div>
                <div className="p-3 rounded-lg bg-[#0e1422] border border-slate-800 space-y-1.5">
                  {selectedTool.security_controls.map((ctrl, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-[11px] text-slate-300">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <span>{ctrl}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-xl bg-[#111827] border border-slate-800/80 text-center space-y-3">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mx-auto">
                <Wrench className="w-5 h-5" />
              </div>
              <h4 className="text-xs font-semibold text-white font-mono uppercase">
                No Tool Selected
              </h4>
              <p className="text-[11px] text-slate-400 font-mono max-w-xs mx-auto">
                Select a governed tool from the inventory on the left to inspect parameter validation schemas, security controls, and permission policies.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
