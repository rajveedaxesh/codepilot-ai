import React from 'react';
import { TestTube2, AlertCircle, CheckCircle, ShieldCheck, Play, Sparkles } from 'lucide-react';
import type { RegressionTest } from '../types';

interface RegressionTestPanelProps {
  test: RegressionTest | null;
  onGenerateTest: () => void;
  isGenerating: boolean;
  onTriggerVerification: () => void;
  isVerifying: boolean;
}

export const RegressionTestPanel: React.FC<RegressionTestPanelProps> = ({
  test,
  onGenerateTest,
  isGenerating,
  onTriggerVerification,
  isVerifying,
}) => {
  if (!test) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl bg-slate-900/40">
        <TestTube2 className="h-8 w-8 text-slate-600 mb-2 stroke-[1.5]" />
        <p className="text-xs text-slate-400 font-medium">No Regression Test Generated</p>
        <p className="text-[11px] text-slate-600 mt-1 max-w-xs">
          Generate a regression test targeting the diagnosed bug to safeguard against future regressions.
        </p>
        <button
          onClick={onGenerateTest}
          disabled={isGenerating}
          className="mt-4 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 disabled:opacity-50 transition-all cursor-pointer"
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span>{isGenerating ? 'Synthesizing Test...' : 'Generate Regression Test'}</span>
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="p-3 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TestTube2 className="h-4 w-4 text-emerald-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Regression Test Suite
          </span>
        </div>
        <span className="font-mono text-[11px] text-slate-400">{test.file_path}</span>
      </div>

      <div className="p-4 flex-1 overflow-y-auto space-y-4">
        {/* Verification Distinction Warning Banner */}
        <div
          className={`p-3 rounded-lg border text-xs flex items-start gap-2.5 ${
            test.is_verified
              ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300'
              : 'bg-amber-950/30 border-amber-500/30 text-amber-300'
          }`}
        >
          {test.is_verified ? (
            <CheckCircle className="h-4 w-4 shrink-0 text-emerald-400 mt-0.5" />
          ) : (
            <AlertCircle className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
          )}
          <div>
            <h5 className="font-semibold text-xs">
              {test.is_verified
                ? 'GENUINE TEST PASS VERIFIED IN ISOLATED SANDBOX'
                : 'GENERATED TEST SUGGESTION — UNVERIFIED'}
            </h5>
            <p className="text-[11px] opacity-90 mt-0.5">
              {test.is_verified
                ? 'This test has been physically executed in the isolated sandbox environment and passed with exit code 0.'
                : 'CodePilot AI never claims code works merely because an LLM generated it. Run isolated verification below to test.'}
            </p>
          </div>
        </div>

        {/* Test Rationale & Assertion Explanation */}
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2">
          <div>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Test Rationale
            </span>
            <p className="text-xs text-slate-300 mt-0.5 font-medium">{test.test_rationale}</p>
          </div>
          <div>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Assertion Intention
            </span>
            <p className="text-xs text-slate-400 mt-0.5">{test.assertion_description}</p>
          </div>
        </div>

        {/* Code Block */}
        <div className="rounded-lg border border-slate-800 bg-slate-950/90 overflow-hidden font-mono text-xs">
          <div className="px-3 py-1.5 bg-slate-900 border-b border-slate-800 text-slate-400 text-[11px] flex justify-between">
            <span>Framework: {test.test_framework}</span>
            <span>{test.file_path}</span>
          </div>
          <pre className="p-3 overflow-x-auto text-slate-200 leading-relaxed max-h-[300px]">
            {test.test_code}
          </pre>
        </div>

        {/* Trigger Verification Button */}
        <div className="pt-2">
          <button
            onClick={onTriggerVerification}
            disabled={isVerifying}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-semibold bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white shadow-lg shadow-emerald-500/20 disabled:opacity-50 transition-all cursor-pointer"
          >
            <Play className="h-4 w-4 fill-current" />
            <span>{isVerifying ? 'Running Sandboxed Verification...' : 'Execute Isolated Verification Run'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
