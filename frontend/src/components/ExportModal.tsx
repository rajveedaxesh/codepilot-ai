import React, { useState } from 'react';
import { Download, Copy, Check, X, FileText, Code2 } from 'lucide-react';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  reportData: {
    session_id: string;
    project_name: string;
    status: string;
    markdown_report: string;
    json_data: any;
  } | null;
}

export const ExportModal: React.FC<ExportModalProps> = ({ isOpen, onClose, reportData }) => {
  const [tab, setTab] = useState<'markdown' | 'json'>('markdown');
  const [copied, setCopied] = useState(false);

  if (!isOpen || !reportData) return null;

  const handleCopy = () => {
    const textToCopy = tab === 'markdown' ? reportData.markdown_report : JSON.stringify(reportData.json_data, null, 2);
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const isMd = tab === 'markdown';
    const content = isMd ? reportData.markdown_report : JSON.stringify(reportData.json_data, null, 2);
    const filename = `codepilot_report_${reportData.project_name.toLowerCase().replace(/\s+/g, '_')}_${reportData.session_id.slice(0, 8)}.${isMd ? 'md' : 'json'}`;
    const blob = new Blob([content], { type: isMd ? 'text/markdown' : 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="flex flex-col w-full max-w-4xl max-h-[85vh] rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-indigo-400" />
            <h3 className="font-bold text-sm text-white">Export Session Report</h3>
            <span className="text-xs text-slate-400">&bull; {reportData.project_name}</span>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Action bar & tabs */}
        <div className="flex items-center justify-between px-6 py-2.5 bg-slate-950/40 border-b border-slate-800 text-xs">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setTab('markdown')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors ${
                tab === 'markdown' ? 'bg-indigo-600/30 text-indigo-300 font-semibold border border-indigo-500/40' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              <span>Markdown Report</span>
            </button>
            <button
              onClick={() => setTab('json')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors ${
                tab === 'json' ? 'bg-indigo-600/30 text-indigo-300 font-semibold border border-indigo-500/40' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Code2 className="h-3.5 w-3.5" />
              <span>JSON Structured Data</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-md shadow-indigo-600/20 transition-all"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Download File</span>
            </button>
          </div>
        </div>

        {/* Content Viewer */}
        <div className="flex-1 p-6 overflow-y-auto font-mono text-xs bg-slate-950/90 text-slate-300 leading-relaxed select-text">
          <pre className="whitespace-pre-wrap break-all">
            {tab === 'markdown' ? reportData.markdown_report : JSON.stringify(reportData.json_data, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
};
