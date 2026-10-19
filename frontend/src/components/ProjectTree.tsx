import React, { useState } from 'react';
import { Folder, FolderOpen, FileCode, FileText, CheckCircle, Search, ChevronRight, ChevronDown } from 'lucide-react';
import type { FileNode } from '../types';

interface ProjectTreeProps {
  tree: FileNode | null;
  selectedFilePath: string | null;
  onSelectFile: (path: string) => void;
}

export const ProjectTree: React.FC<ProjectTreeProps> = ({
  tree,
  selectedFilePath,
  onSelectFile,
}) => {
  const [search, setSearch] = useState('');
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  const toggleCollapse = (path: string) => {
    setCollapsed(prev => ({ ...prev, [path]: !prev[path] }));
  };

  const getFileIcon = (node: FileNode) => {
    if (node.is_test) {
      return <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0" />;
    }
    const ext = node.name.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'py':
        return <FileCode className="h-4 w-4 text-amber-400 shrink-0" />;
      case 'ts':
      case 'tsx':
        return <FileCode className="h-4 w-4 text-cyan-400 shrink-0" />;
      case 'js':
      case 'jsx':
        return <FileCode className="h-4 w-4 text-yellow-300 shrink-0" />;
      case 'toml':
      case 'json':
      case 'yaml':
      case 'yml':
        return <FileText className="h-4 w-4 text-indigo-400 shrink-0" />;
      default:
        return <FileText className="h-4 w-4 text-slate-400 shrink-0" />;
    }
  };

  const renderNode = (node: FileNode, level = 0) => {
    const isDir = node.type === 'directory';
    const isExpanded = !collapsed[node.path];
    const isSelected = selectedFilePath === node.path;

    // Filter match check
    if (search && !node.name.toLowerCase().includes(search.toLowerCase())) {
      // If it's a directory, check if any child matches
      if (!isDir || !node.children?.some(c => c.name.toLowerCase().includes(search.toLowerCase()))) {
        return null;
      }
    }

    return (
      <div key={node.path || node.name} className="select-none">
        <div
          onClick={() => {
            if (isDir) {
              toggleCollapse(node.path);
            } else {
              onSelectFile(node.path);
            }
          }}
          style={{ paddingLeft: `${Math.max(8, level * 16)}px` }}
          className={`flex items-center gap-2 py-1.5 px-2 my-0.5 rounded-md cursor-pointer text-xs transition-colors group ${
            isSelected
              ? 'bg-indigo-600/30 text-indigo-200 font-medium border border-indigo-500/40'
              : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
          }`}
        >
          {isDir ? (
            <>
              {isExpanded ? (
                <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
              ) : (
                <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
              )}
              {isExpanded ? (
                <FolderOpen className="h-4 w-4 text-indigo-400 shrink-0" />
              ) : (
                <Folder className="h-4 w-4 text-indigo-400 shrink-0" />
              )}
            </>
          ) : (
            <>
              <span className="w-3.5" />
              {getFileIcon(node)}
            </>
          )}

          <span className="truncate flex-1 font-mono text-[11px]">{node.name}</span>

          {node.is_test && (
            <span className="text-[9px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.2 rounded border border-emerald-500/20">
              test
            </span>
          )}
        </div>

        {isDir && isExpanded && node.children && (
          <div>
            {node.children.map(child => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden shadow-sm">
      <div className="p-3 border-b border-slate-800/80 bg-slate-950/40">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Repository Explorer
          </span>
          <span className="text-[10px] text-slate-500 font-mono">Sanitized Tree</span>
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-slate-500" />
          <input
            type="text"
            placeholder="Filter files..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1 text-xs bg-slate-900 border border-slate-700/80 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {tree ? (
          renderNode(tree)
        ) : (
          <div className="flex flex-col items-center justify-center h-48 text-center p-4 text-slate-500">
            <Folder className="h-8 w-8 text-slate-600 mb-2 stroke-[1.5]" />
            <p className="text-xs">No repository uploaded yet.</p>
            <p className="text-[11px] text-slate-600 mt-1">Upload a ZIP to inspect repository hierarchy.</p>
          </div>
        )}
      </div>
    </div>
  );
};
