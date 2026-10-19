import React, { useState } from 'react';
import { Terminal, Shield, CheckCircle, XCircle, Clock, Check, Copy } from 'lucide-react';
import type { VerificationRun } from '../types';

interface VerificationTerminalProps {
  run: VerificationRun | null;
  isRunning: boolean;
  onReverify: (cmd?: string) => void;
}

export const VerificationTerminal: React.FC<VerificationTerminalProps> = ({
  run,
  isRunning,
  onReverify,
}) => {
  const [tab, setTab] = useState<'patched' | 'baseline' | 'stderr'>('patched');
  const [copied, setCopied] = useState(false);

  const handleCopyLogs = () => {
    if (run) {
      const fullLog = `COMMAND: ${run.command}\nEXIT CODE: ${run.exit_code}\nDURATION: ${run.duration_ms}ms\n\nSTDOUT:\n${run.stdout}\n\nSTDERR:\n${run.stderr}`;
      navigator.clipboard.writeText(fullLog);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!run && !isRunning) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl bg-slate-900/40">
        <Terminal className="h-8 w-8 text-slate-600 mb-2 stroke-[1.5]" />
        <p className="text-xs text-slate-400 font-medium">No Verification Run Executed</p>
        <p className="text-[11px] text-slate-600 mt-1 max-w-xs">
          Execute isolated verification to record genuine exit codes, stdout, and execution duration.
        </p>
      </div>
    );
  }

  const getStatusBadge = () => {
    if (isRunning) {
      return (
        <span className="px-2.5 py-1 rounded text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 animate-pulse">
          RUNNING IN DISPOSABLE WORKSPACE...
        </span>
      );
    }
    if (!run) return null;

    if (run.is_verified) {
      return (
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold">
          <CheckCircle className="h-4 w-4 text-emerald-400" />
          <span>FIX VERIFIED (Exit Code 0)</span>
        </div>
      );
    }

    if (run.status === 'failed') {
      return (
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-red-500/20 text-red-300 border border-red-500/30 text-xs font-semibold">
          <XCircle className="h-4 w-4 text-red-400" />
          <span>VERIFICATION FAILED (Exit Code {run.exit_code})</span>
        </div>
      );
    }

    return (
      <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-semibold">
        <span>UNVERIFIED / TIMED OUT</span>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="p-3 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-cyan-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Isolated Verification Engine
          </span>
        </div>
        <div>{getStatusBadge()}</div>
      </div>

      <div className="p-4 flex-1 overflow-y-auto space-y-4">
        {/* Run Metadata Bar */}
        {run && (
          <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-500">Executed:</span>
              <span className="font-mono text-cyan-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                {run.command}
              </span>
            </div>

            <div className="flex items-center gap-4 text-slate-400">
              <div className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5 text-slate-500" />
                <span>Duration:</span>
                <span className="font-mono text-slate-200 font-semibold">{run.duration_ms}ms</span>
              </div>

              <div className="flex items-center gap-1.5">
                <span>Exit Code:</span>
                <span
                  className={`font-mono font-bold px-1.5 py-0.5 rounded ${
                    run.exit_code === 0 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
                  }`}
                >
                  {run.exit_code}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Summary Callout */}
        {run?.summary && (
          <div
            className={`p-3 rounded-lg border text-xs font-medium ${
              run.is_verified
                ? 'bg-emerald-950/20 border-emerald-500/20 text-emerald-300'
                : 'bg-red-950/20 border-red-500/20 text-red-300'
            }`}
          >
            {run.summary}
          </div>
        )}

        {/* Output Tabs & Terminal */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/95 overflow-hidden font-mono text-xs shadow-inner">
          <div className="flex items-center justify-between px-3 py-2 bg-slate-900 border-b border-slate-800">
            <div className="flex items-center gap-1">
              <button
                onClick={() => setTab('patched')}
                className={`px-2.5 py-1 rounded text-xs transition-colors ${
                  tab === 'patched' ? 'bg-slate-800 text-slate-200 font-medium' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                Patched Output (stdout)
              </button>

              {run?.baseline_output !== undefined && (
                <button
                  onClick={() => setTab('baseline')}
                  className={`px-2.5 py-1 rounded text-xs transition-colors ${
                    tab === 'baseline' ? 'bg-slate-800 text-slate-200 font-medium' : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  Baseline Output {run?.baseline_exit_code !== null && `[Exit: ${run.baseline_exit_code}]`}
                </button>
              )}

              {run?.stderr && (
                <button
                  onClick={() => setTab('stderr')}
                  className={`px-2.5 py-1 rounded text-xs transition-colors ${
                    tab === 'stderr' ? 'bg-red-950/40 text-red-300 font-medium' : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  Standard Error
                </button>
              )}
            </div>

            <button
              onClick={handleCopyLogs}
              className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
              <span>{copied ? 'Copied' : 'Copy Output'}</span>
            </button>
          </div>

          <div className="p-3.5 max-h-[350px] overflow-y-auto font-mono text-[11px] leading-relaxed select-text">
            {tab === 'patched' && (
              <pre className="text-slate-200 whitespace-pre-wrap break-all">
                {run?.stdout || (isRunning ? 'Executing test suite in isolated workspace...' : '(No stdout recorded)')}
              </pre>
            )}

            {tab === 'baseline' && (
              <pre className="text-amber-200/90 whitespace-pre-wrap break-all">
                {run?.baseline_output || '(No baseline output recorded)'}
              </pre>
            )}

            {tab === 'stderr' && (
              <pre className="text-red-300 whitespace-pre-wrap break-all">
                {run?.stderr || '(No stderr recorded)'}
              </pre>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
