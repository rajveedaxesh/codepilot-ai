import React from 'react';
import { ShieldCheck, Lock, AlertTriangle, FileCode, Server, Terminal, EyeOff, CheckCircle } from 'lucide-react';

export const SecurityView: React.FC = () => {
  const safeguards = [
    {
      title: "ZipSlip & Path Traversal Prevention",
      icon: <Lock className="h-5 w-5 text-indigo-400" />,
      status: "Active",
      description: "Every archive member and file path is validated using strict canonical path boundaries (os.path.commonpath). Relative traversal sequences like '../' and symlinks escaping the workspace root are blocked with 403 Forbidden."
    },
    {
      title: "Secret & Credential Redaction",
      icon: <EyeOff className="h-5 w-5 text-amber-400" />,
      status: "Active",
      description: "Automated regex filters detect and redact Anthropic API keys, AWS access tokens, private keys, and passwords from uploaded code, unified diffs, execution logs, and API payloads before display."
    },
    {
      title: "Explicit Patch Approval Gate",
      icon: <ShieldCheck className="h-5 w-5 text-emerald-400" />,
      status: "Enforced",
      description: "The AI agent is structurally forbidden from silently modifying code. A human developer must explicitly inspect the unified diff and click 'Approve Patch' before any disk modification or patch application occurs."
    },
    {
      title: "Disposable Sandbox Workspaces",
      icon: <Server className="h-5 w-5 text-cyan-400" />,
      status: "Active",
      description: "Verification tests run strictly inside ephemeral sandbox copies in the data/sandbox directory. After test completion, the temporary directory is automatically pruned, preventing workspace pollution."
    },
    {
      title: "Strict Command Allowlisting",
      icon: <Terminal className="h-5 w-5 text-purple-400" />,
      status: "Enforced",
      description: "Only approved test commands ('pytest', 'python -m pytest', 'npm test') are permitted. Shell metacharacters (';', '&&', '||', '|', redirect operators, backticks) are strictly rejected with shell=False execution."
    },
    {
      title: "Resource & Execution Timeouts",
      icon: <AlertTriangle className="h-5 w-5 text-yellow-400" />,
      status: "30s Limit",
      description: "All test verification processes enforce a strict 30-second timeout. Any hanging process or runaway infinite loop is terminated, preventing denial-of-service on the host."
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-emerald-950/20 to-slate-900 border border-slate-800 shadow-lg">
        <div className="flex items-center gap-2 mb-2">
          <ShieldCheck className="h-6 w-6 text-emerald-400" />
          <h2 className="text-xl font-bold tracking-tight text-white">
            Security Architecture & Threat Model
          </h2>
          <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-300 border border-emerald-500/20">
            Defense-in-Depth Active
          </span>
        </div>
        <p className="text-xs text-slate-400 max-w-3xl leading-relaxed">
          Uploaded source repositories are treated as inherently untrusted data. CodePilot AI implements multi-layered isolation, deterministic boundary checks, and human-in-the-loop safety gates to ensure safe operation.
        </p>
      </div>

      {/* Security Safeguards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {safeguards.map((item, idx) => (
          <div key={idx} className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition-all flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/50">
                  {item.icon}
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {item.status}
                </span>
              </div>
              <h4 className="text-sm font-semibold text-slate-200 mb-1.5">{item.title}</h4>
              <p className="text-xs text-slate-400 leading-relaxed">{item.description}</p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center gap-1.5 text-[11px] text-emerald-400/90 font-medium">
              <CheckCircle className="h-3.5 w-3.5" />
              <span>Verified Security Boundary</span>
            </div>
          </div>
        ))}
      </div>

      {/* Untrusted Repository Contract */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
          <FileCode className="h-4 w-4 text-indigo-400" />
          <span>Core Agent Security Invariants</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300">
          <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800">
            <h5 className="font-semibold text-slate-200 mb-1">1. Untrusted Prompt Injection Defense</h5>
            <p className="text-slate-400 leading-relaxed">
              Code comments, README files, and commit logs are strictly isolated as literal data strings in prompts. They are never interpreted as system instructions or privileged agent directives.
            </p>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800">
            <h5 className="font-semibold text-slate-200 mb-1">2. No Unverified Success Claims</h5>
            <p className="text-slate-400 leading-relaxed">
              Generated tests and proposed patches are tagged as UNVERIFIED until physically executed in an isolated disposable workspace and returned with exit code 0.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
