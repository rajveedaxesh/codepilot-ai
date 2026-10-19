import React, { useState } from 'react';
import { AlertTriangle, Sparkles, CheckCircle2, ShieldAlert, FileText, ChevronRight, Play } from 'lucide-react';
import type { BugFinding } from '../types';

interface BugAnalysisPanelProps {
  finding: BugFinding | null;
  isAnalyzing: boolean;
  onAnalyze: (description: string, targetFile?: string) => void;
  targetFile: string | null;
  onSelectTargetFile: (path: string | null) => void;
  onGeneratePatch: () => void;
  isPatchGenerating: boolean;
}

export const BugAnalysisPanel: React.FC<BugAnalysisPanelProps> = ({
  finding,
  isAnalyzing,
  onAnalyze,
  targetFile,
  onSelectTargetFile,
  onGeneratePatch,
  isPatchGenerating,
}) => {
  const [description, setDescription] = useState(
    'ZeroDivisionError occurs when denominator is zero in divide() function or empty dataset in average computation'
  );

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-500/20 text-red-300 border border-red-500/30">CRITICAL</span>;
      case 'high':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">HIGH</span>;
      case 'medium':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-yellow-500/20 text-yellow-300 border border-yellow-500/30">MEDIUM</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30">LOW</span>;
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="p-3 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-indigo-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Bug Analysis & Diagnosis Agent
          </span>
        </div>
        {finding && (
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-400">Confidence:</span>
            <span className="font-mono text-xs font-semibold text-emerald-400">
              {(finding.confidence * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      <div className="p-4 flex-1 overflow-y-auto space-y-4">
        {/* Input Form */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-slate-300 flex items-center justify-between">
            <span>Describe Bug or Observed Failure</span>
            {targetFile && (
              <span className="text-[10px] text-amber-400 font-mono">
                Focus: {targetFile}
              </span>
            )}
          </label>
          <textarea
            rows={3}
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="e.g. ZeroDivisionError when denominator is zero, or IndexError in loop boundary..."
            className="w-full p-2.5 text-xs bg-slate-950/80 border border-slate-700/80 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors font-mono resize-none"
          />

          <div className="flex items-center justify-between pt-1">
            {targetFile ? (
              <button
                onClick={() => onSelectTargetFile(null)}
                className="text-[11px] text-slate-400 hover:text-slate-200 underline"
              >
                Clear target file focus
              </button>
            ) : (
              <span className="text-[11px] text-slate-500">
                Tip: Click "Set as Diagnosis Target" on any file in viewer to focus.
              </span>
            )}

            <button
              onClick={() => onAnalyze(description, targetFile || undefined)}
              disabled={isAnalyzing || !description.trim()}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 disabled:opacity-50 transition-all cursor-pointer"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>{isAnalyzing ? 'Analyzing Repository...' : 'Run Bug Diagnosis'}</span>
            </button>
          </div>
        </div>

        {/* Diagnosis Results */}
        {finding ? (
          <div className="mt-4 space-y-3 pt-3 border-t border-slate-800">
            {/* Severity & Confidence Banner */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Severity:</span>
                {getSeverityBadge(finding.severity)}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Affected Files:</span>
                <span className="font-mono text-xs text-slate-200">
                  {finding.affected_files.join(', ')}
                </span>
              </div>
            </div>

            {/* Suspected Root Cause */}
            <div className="p-3 rounded-lg bg-indigo-950/20 border border-indigo-500/20">
              <h5 className="text-[11px] font-semibold uppercase tracking-wider text-indigo-400 mb-1 flex items-center gap-1.5">
                <ShieldAlert className="h-3.5 w-3.5" />
                Suspected Root Cause
              </h5>
              <p className="text-xs text-slate-200 leading-relaxed font-medium">
                {finding.suspected_root_cause}
              </p>
            </div>

            {/* Detailed Explanation */}
            <div>
              <h5 className="text-xs font-semibold text-slate-300 mb-1">Architectural Analysis</h5>
              <p className="text-xs text-slate-400 leading-relaxed bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/60">
                {finding.explanation}
              </p>
            </div>

            {/* Concrete Evidence Snippets */}
            <div>
              <h5 className="text-xs font-semibold text-slate-300 mb-2 flex items-center justify-between">
                <span>Observed Repository Evidence</span>
                <span className="text-[10px] text-slate-500 font-mono">
                  {finding.evidence?.length || 0} snippets
                </span>
              </h5>
              <div className="space-y-2">
                {finding.evidence?.map((ev, idx) => (
                  <div key={idx} className="rounded-lg bg-slate-950/80 border border-slate-800 p-2.5 text-xs font-mono">
                    <div className="flex items-center justify-between text-slate-400 text-[11px] pb-1.5 mb-1.5 border-b border-slate-800/80">
                      <span className="text-indigo-300 font-semibold">{ev.file_path}</span>
                      <span>L{ev.line_start} - L{ev.line_end}</span>
                    </div>
                    <pre className="text-slate-300 overflow-x-auto text-[11px] leading-relaxed">
                      {ev.code_snippet}
                    </pre>
                    <p className="text-[11px] text-slate-500 mt-1.5 font-sans">
                      &rarr; {ev.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Next Action: Generate Patch */}
            <div className="pt-2">
              <button
                onClick={onGeneratePatch}
                disabled={isPatchGenerating}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-semibold bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white shadow-lg shadow-indigo-500/20 disabled:opacity-50 transition-all cursor-pointer"
              >
                <Sparkles className="h-4 w-4" />
                <span>{isPatchGenerating ? 'Synthesizing Patch...' : 'Generate Proposed Patch'}</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-lg">
            <FileText className="h-8 w-8 text-slate-600 mb-2 stroke-[1.5]" />
            <p className="text-xs text-slate-400 font-medium">No active diagnosis yet</p>
            <p className="text-[11px] text-slate-600 mt-1 max-w-xs">
              Enter a description and click "Run Bug Diagnosis" to trigger repository intelligence.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
