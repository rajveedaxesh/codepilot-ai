import React from 'react';
import { GitPullRequest, Copy, Check } from 'lucide-react';

interface DiffViewerProps {
  diffText: string;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ diffText }) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(diffText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = diffText.split('\n');

  return (
    <div className="flex flex-col rounded-lg border border-slate-800 bg-slate-950/80 overflow-hidden font-mono text-xs">
      {/* Top Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-slate-900 border-b border-slate-800 text-slate-400">
        <div className="flex items-center gap-2">
          <GitPullRequest className="h-4 w-4 text-indigo-400" />
          <span className="font-semibold text-slate-300">Unified Diff Patch</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
        >
          {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
          <span>{copied ? 'Copied' : 'Copy Diff'}</span>
        </button>
      </div>

      {/* Diff Content */}
      <div className="p-3 overflow-x-auto max-h-[420px] overflow-y-auto space-y-0.5">
        {lines.map((line, idx) => {
          let lineStyle = 'text-slate-300 px-2 py-0.5';
          if (line.startsWith('+++') || line.startsWith('---')) {
            lineStyle = 'font-bold text-slate-200 bg-slate-800/80 px-2 py-0.5';
          } else if (line.startsWith('@@')) {
            lineStyle = 'diff-info font-medium px-2 py-0.5 bg-blue-500/10 text-blue-300';
          } else if (line.startsWith('+')) {
            lineStyle = 'diff-add px-2 py-0.5';
          } else if (line.startsWith('-')) {
            lineStyle = 'diff-del px-2 py-0.5';
          }

          return (
            <div key={idx} className={`flex items-start ${lineStyle}`}>
              <span className="w-8 shrink-0 select-none text-slate-600 text-[10px] text-right pr-2">
                {idx + 1}
              </span>
              <pre className="whitespace-pre-wrap break-all flex-1 font-mono">{line}</pre>
            </div>
          );
        })}
      </div>
    </div>
  );
};
