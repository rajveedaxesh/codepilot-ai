import React from 'react';
import { ShieldCheck, Cpu, Terminal, BarChart3, Settings, Sparkles, FolderDown } from 'lucide-react';

interface NavbarProps {
  currentTab: 'dashboard' | 'benchmarks' | 'security' | 'settings';
  setCurrentTab: (tab: 'dashboard' | 'benchmarks' | 'security' | 'settings') => void;
  providerName: string;
  onLoadDemo: () => void;
  isDemoLoading: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  providerName,
  onLoadDemo,
  isDemoLoading
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20">
            <div className="flex h-full w-full items-center justify-center rounded-[10px] bg-slate-950">
              <Cpu className="h-5 w-5 text-indigo-400 animate-pulse" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                CodePilot AI
              </span>
              <span className="rounded-full bg-indigo-500/10 px-2 py-0.5 text-[10px] font-semibold text-indigo-400 border border-indigo-500/20">
                Autonomous Agent
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Repository Comprehension &bull; Diagnosis &bull; Verified Patching
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 sm:gap-2">
          <button
            onClick={() => setCurrentTab('dashboard')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              currentTab === 'dashboard'
                ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Terminal className="h-3.5 w-3.5" />
            <span>Workspace</span>
          </button>

          <button
            onClick={() => setCurrentTab('benchmarks')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              currentTab === 'benchmarks'
                ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <BarChart3 className="h-3.5 w-3.5" />
            <span>Evaluation (10 Fixtures)</span>
          </button>

          <button
            onClick={() => setCurrentTab('security')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              currentTab === 'security'
                ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Security Model</span>
          </button>
        </nav>

        {/* Action & Status */}
        <div className="flex items-center gap-3">
          <button
            onClick={onLoadDemo}
            disabled={isDemoLoading}
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gradient-to-r from-emerald-500/10 to-teal-500/10 text-emerald-300 border border-emerald-500/30 hover:border-emerald-500/50 hover:bg-emerald-500/20 transition-all shadow-sm disabled:opacity-50"
            title="Instantly loads pre-packaged sample repository with deliberate bugs"
          >
            <FolderDown className="h-3.5 w-3.5 text-emerald-400" />
            <span>{isDemoLoading ? 'Loading Demo...' : 'Load Sample Demo'}</span>
          </button>

          <div className="flex items-center gap-2 rounded-lg bg-slate-900 border border-slate-800 px-2.5 py-1 text-xs">
            <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-400 hidden lg:inline">Provider:</span>
            <span className="font-mono text-slate-200 text-[11px] truncate max-w-[140px]" title={providerName}>
              {providerName}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
