import React from 'react';
import Editor from '@monaco-editor/react';
import { FileCode, Shield, Target, Copy, Check } from 'lucide-react';
import type { FileContent } from '../types';

interface CodeViewerProps {
  file: FileContent | null;
  onSetAsTarget: (path: string) => void;
  isTarget: boolean;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  file,
  onSetAsTarget,
  isTarget,
}) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    if (file?.content) {
      navigator.clipboard.writeText(file.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getMonacoLang = (lang?: string) => {
    switch (lang) {
      case 'python': return 'python';
      case 'typescript': return 'typescript';
      case 'javascript': return 'javascript';
      case 'json': return 'json';
      case 'yaml': return 'yaml';
      case 'toml': return 'ini';
      case 'markdown': return 'markdown';
      case 'html': return 'html';
      case 'css': return 'css';
      default: return 'plaintext';
    }
  };

  if (!file) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-slate-900/60 border border-slate-800/80 rounded-xl p-8 text-center text-slate-500">
        <FileCode className="h-12 w-12 text-slate-700 mb-3 stroke-[1.2]" />
        <h4 className="text-sm font-medium text-slate-400">No File Selected</h4>
        <p className="text-xs text-slate-600 mt-1 max-w-sm">
          Select a file from the repository explorer on the left to inspect its contents, line definitions, and references.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden shadow-sm">
      {/* File Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800/80 bg-slate-950/60">
        <div className="flex items-center gap-2">
          <FileCode className="h-4 w-4 text-indigo-400" />
          <span className="font-mono text-xs text-slate-200 font-medium">{file.file_path}</span>
          <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">
            {file.language} &bull; {(file.size / 1024).toFixed(1)} KB
          </span>
          {file.is_test && (
            <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20 font-medium">
              Test Suite
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onSetAsTarget(file.file_path)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
              isTarget
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                : 'bg-slate-800/70 hover:bg-slate-700 text-slate-300'
            }`}
            title="Focus bug analysis on this file"
          >
            <Target className="h-3.5 w-3.5 text-amber-400" />
            <span>{isTarget ? 'Target File Active' : 'Set as Diagnosis Target'}</span>
          </button>

          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs bg-slate-800/70 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Copy file contents"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <div className="flex items-center gap-1 text-[11px] text-slate-500 ml-2" title="Source files treated as untrusted data">
            <Shield className="h-3 w-3 text-emerald-400" />
            <span>Redacted & Sanitized</span>
          </div>
        </div>
      </div>

      {/* Monaco Editor Container */}
      <div className="flex-1 w-full min-h-[350px]">
        <Editor
          height="100%"
          language={getMonacoLang(file.language)}
          theme="vs-dark"
          value={file.content}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 12,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            renderWhitespace: 'selection',
            fontFamily: "'JetBrains Mono', Consolas, monospace",
            padding: { top: 12, bottom: 12 },
          }}
        />
      </div>
    </div>
  );
};
