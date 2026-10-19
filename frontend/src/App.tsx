import React, { useState, useEffect } from 'react';
import {
  Upload, FolderDown, Terminal, Shield, RefreshCw, FileText, CheckCircle2,
  AlertTriangle, Download, Sparkles, Folder, Cpu, GitCommit
} from 'lucide-react';

import type { Project, FileNode, FileContent, AnalysisSession, BugFinding, ProposedPatch, RegressionTest, VerificationRun } from './types';
import { api } from './api/client';
import { Navbar } from './components/Navbar';
import { ProjectTree } from './components/ProjectTree';
import { CodeViewer } from './components/CodeViewer';
import { BugAnalysisPanel } from './components/BugAnalysisPanel';
import { PatchReviewModal } from './components/PatchReviewModal';
import { RegressionTestPanel } from './components/RegressionTestPanel';
import { VerificationTerminal } from './components/VerificationTerminal';
import { BenchmarkRunner } from './components/BenchmarkRunner';
import { SecurityView } from './components/SecurityView';
import { ExportModal } from './components/ExportModal';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'dashboard' | 'benchmarks' | 'security' | 'settings'>('dashboard');
  const [providerName, setProviderName] = useState<string>('mock (offline provider)');

  // Projects & Sessions state
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [fileTree, setFileTree] = useState<FileNode | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileContent | null>(null);
  const [targetFile, setTargetFile] = useState<string | null>(null);

  // Active Session State
  const [session, setSession] = useState<AnalysisSession | null>(null);
  const [activeFinding, setActiveFinding] = useState<BugFinding | null>(null);
  const [activePatch, setActivePatch] = useState<ProposedPatch | null>(null);
  const [activeTest, setActiveTest] = useState<RegressionTest | null>(null);
  const [activeRun, setActiveRun] = useState<VerificationRun | null>(null);

  // Loading States
  const [isDemoLoading, setIsDemoLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isPatchGenerating, setIsPatchGenerating] = useState(false);
  const [isApplyingPatch, setIsApplyingPatch] = useState(false);
  const [isGeneratingTest, setIsGeneratingTest] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  // Export Modal State
  const [exportData, setExportData] = useState<any | null>(null);
  const [isExportOpen, setIsExportOpen] = useState(false);

  // Error / Notification Banner
  const [alert, setAlert] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  const showAlert = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setAlert({ message, type });
    setTimeout(() => setAlert(null), 5000);
  };

  // Initial Data Load
  useEffect(() => {
    loadHealth();
    loadProjects();
  }, []);

  const loadHealth = async () => {
    try {
      const data = await api.getHealth();
      setProviderName(data.llm_provider);
    } catch {
      setProviderName('mock (offline provider)');
    }
  };

  const loadProjects = async () => {
    try {
      const list = await api.getProjects();
      setProjects(list);
      if (list.length > 0 && !activeProject) {
        selectProject(list[0]);
      }
    } catch (e: any) {
      console.error('Failed to load projects', e);
    }
  };

  const selectProject = async (proj: Project) => {
    setActiveProject(proj);
    try {
      const tree = await api.getProjectTree(proj.id);
      setFileTree(tree);

      // Select first interesting source file automatically
      const findFirstCodeFile = (node: FileNode): string | null => {
        if (node.type === 'file' && (node.name.endsWith('.py') || node.name.endsWith('.ts') || node.name.endsWith('.js'))) {
          return node.path;
        }
        if (node.children) {
          for (const c of node.children) {
            const res = findFirstCodeFile(c);
            if (res) return res;
          }
        }
        return null;
      };

      const firstFile = findFirstCodeFile(tree);
      if (firstFile) {
        loadFile(proj.id, firstFile);
      }

      // Check or create session
      const sessions = await api.getSessions(proj.id);
      if (sessions.length > 0) {
        loadSession(sessions[0].id);
      } else {
        const newSession = await api.createSession(proj.id);
        loadSession(newSession.session_id);
      }
    } catch (e: any) {
      showAlert(`Error loading project: ${e.message}`, 'error');
    }
  };

  const loadFile = async (projectId: string, path: string) => {
    try {
      const fileData = await api.getFileContent(projectId, path);
      setSelectedFile(fileData);
    } catch (e: any) {
      showAlert(`Error reading file ${path}: ${e.message}`, 'error');
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      const sessionData = await api.getSession(sessionId);
      setSession(sessionData);

      if (sessionData.findings && sessionData.findings.length > 0) {
        setActiveFinding(sessionData.findings[sessionData.findings.length - 1]);
      } else {
        setActiveFinding(null);
      }

      if (sessionData.patches && sessionData.patches.length > 0) {
        setActivePatch(sessionData.patches[sessionData.patches.length - 1]);
      } else {
        setActivePatch(null);
      }

      if (sessionData.regression_tests && sessionData.regression_tests.length > 0) {
        setActiveTest(sessionData.regression_tests[sessionData.regression_tests.length - 1]);
      } else {
        setActiveTest(null);
      }

      if (sessionData.verification_runs && sessionData.verification_runs.length > 0) {
        setActiveRun(sessionData.verification_runs[sessionData.verification_runs.length - 1]);
      } else {
        setActiveRun(null);
      }

      if (sessionData.target_file) {
        setTargetFile(sessionData.target_file);
      }
    } catch (e: any) {
      console.error('Session load error', e);
    }
  };

  const handleUploadZip = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const proj = await api.uploadRepository(file);
      showAlert(`Repository '${proj.name}' uploaded and inspected safely!`, 'success');
      setProjects(prev => [proj, ...prev]);
      selectProject(proj);
    } catch (err: any) {
      showAlert(`Upload failed: ${err.message}`, 'error');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleLoadDemo = async () => {
    setIsDemoLoading(true);
    try {
      const proj = await api.loadDemoProject();
      showAlert(`Demo Math & Utility Service loaded successfully!`, 'success');
      setProjects(prev => [proj, ...prev]);
      selectProject(proj);
    } catch (err: any) {
      showAlert(`Failed to load demo: ${err.message}`, 'error');
    } finally {
      setIsDemoLoading(false);
    }
  };

  const handleAnalyzeBug = async (desc: string, target?: string) => {
    if (!session) return;
    setIsAnalyzing(true);
    try {
      const finding = await api.analyzeBug(session.id, desc, target);
      setActiveFinding(finding);
      showAlert(`Bug analysis complete: ${finding.suspected_root_cause}`, 'success');
      loadSession(session.id);
    } catch (err: any) {
      showAlert(`Diagnosis error: ${err.message}`, 'error');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGeneratePatch = async () => {
    if (!session) return;
    setIsPatchGenerating(true);
    try {
      const patch = await api.generatePatch(session.id, activeFinding?.id);
      setActivePatch(patch);
      showAlert(`Proposed patch generated! User approval required.`, 'success');
      loadSession(session.id);
    } catch (err: any) {
      showAlert(`Patch generation error: ${err.message}`, 'error');
    } finally {
      setIsPatchGenerating(false);
    }
  };

  const handleApprovePatch = async (patchId: string, approved: boolean, reason?: string) => {
    if (!session) return;
    try {
      const updated = await api.approvePatch(session.id, patchId, approved, reason);
      setActivePatch(updated);
      showAlert(
        approved ? `Patch explicitly APPROVED by user.` : `Patch rejected by user.`,
        approved ? 'success' : 'info'
      );
      loadSession(session.id);
    } catch (err: any) {
      showAlert(`Approval error: ${err.message}`, 'error');
    }
  };

  const handleApplyPatch = async (patchId: string) => {
    if (!session) return;
    setIsApplyingPatch(true);
    try {
      const res = await api.applyPatch(session.id, patchId);
      showAlert(`Patch cleanly applied to: ${res.modified_files.join(', ')}`, 'success');
      if (activeProject) {
        selectProject(activeProject);
      }
      loadSession(session.id);
    } catch (err: any) {
      showAlert(`Apply error: ${err.message}`, 'error');
    } finally {
      setIsApplyingPatch(false);
    }
  };

  const handleGenerateTest = async () => {
    if (!session) return;
    setIsGeneratingTest(true);
    try {
      const test = await api.generateRegressionTest(session.id, activePatch?.id);
      setActiveTest(test);
      showAlert(`Regression test generated: ${test.file_path}`, 'success');
      loadSession(session.id);
    } catch (err: any) {
      showAlert(`Test generation error: ${err.message}`, 'error');
    } finally {
      setIsGeneratingTest(false);
    }
  };

  const handleRunVerification = async (cmd?: string) => {
    if (!session) return;
    setIsVerifying(true);
    try {
      const run = await api.runVerification(session.id, cmd);
      setActiveRun(run);
      if (run.is_verified) {
        showAlert(`Fix VERIFIED! Sandbox test exited with code 0.`, 'success');
      } else {
        showAlert(`Verification finished with non-zero exit code: ${run.exit_code}`, 'error');
      }
      loadSession(session.id);
    } catch (err: any) {
      showAlert(`Verification error: ${err.message}`, 'error');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleOpenExport = async () => {
    if (!session) return;
    try {
      const data = await api.exportSessionReport(session.id);
      setExportData(data);
      setIsExportOpen(true);
    } catch (err: any) {
      showAlert(`Export error: ${err.message}`, 'error');
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#0b0f19] text-slate-100">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        providerName={providerName}
        onLoadDemo={handleLoadDemo}
        isDemoLoading={isDemoLoading}
      />

      {/* Floating Alert / Toast */}
      {alert && (
        <div className="fixed bottom-5 right-5 z-50 max-w-md animate-bounce">
          <div
            className={`px-4 py-3 rounded-xl shadow-2xl text-xs font-medium border flex items-center gap-2 ${
              alert.type === 'success'
                ? 'bg-emerald-950/90 text-emerald-200 border-emerald-500/40'
                : alert.type === 'error'
                ? 'bg-red-950/90 text-red-200 border-red-500/40'
                : 'bg-indigo-950/90 text-indigo-200 border-indigo-500/40'
            }`}
          >
            <span>{alert.message}</span>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 p-4 sm:p-6 overflow-hidden">
        {currentTab === 'benchmarks' && <BenchmarkRunner />}
        {currentTab === 'security' && <SecurityView />}

        {currentTab === 'dashboard' && (
          <div className="flex flex-col h-[calc(100vh-6rem)] space-y-4">
            {/* Top Workspace Summary Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Active Project:</span>
                  <select
                    value={activeProject?.id || ''}
                    onChange={e => {
                      const p = projects.find(x => x.id === e.target.value);
                      if (p) selectProject(p);
                    }}
                    className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 font-medium focus:outline-none focus:border-indigo-500"
                  >
                    {projects.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.file_count} files)
                      </option>
                    ))}
                    {projects.length === 0 && <option value="">No projects loaded</option>}
                  </select>
                </div>

                {activeProject && (
                  <div className="hidden lg:flex items-center gap-2 text-xs text-slate-400">
                    <span className="text-slate-600">&bull;</span>
                    <span>Languages:</span>
                    <span className="text-slate-200 font-mono">
                      {activeProject.languages?.join(', ') || 'None'}
                    </span>
                    <span className="text-slate-600">&bull;</span>
                    <span>Manifest:</span>
                    <span className="text-slate-200 font-mono">
                      {activeProject.manifests?.[0] || 'Generic'}
                    </span>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2">
                {/* Upload ZIP */}
                <label className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 cursor-pointer transition-colors shadow-sm">
                  <Upload className="h-3.5 w-3.5 text-indigo-400" />
                  <span>{isUploading ? 'Extracting...' : 'Upload Repo ZIP'}</span>
                  <input
                    type="file"
                    accept=".zip"
                    onChange={handleUploadZip}
                    disabled={isUploading}
                    className="hidden"
                  />
                </label>

                {session && (
                  <button
                    onClick={handleOpenExport}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/30 transition-colors shadow-sm cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5 text-indigo-400" />
                    <span>Export Report</span>
                  </button>
                )}
              </div>
            </div>

            {/* 3-Column Studio Grid */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4 flex-1 min-h-0">
              {/* Column 1: Explorer (3 cols) */}
              <div className="md:col-span-3 h-full min-h-[350px]">
                <ProjectTree
                  tree={fileTree}
                  selectedFilePath={selectedFile?.file_path || null}
                  onSelectFile={path => {
                    if (activeProject) loadFile(activeProject.id, path);
                  }}
                />
              </div>

              {/* Column 2: Code & Diff Viewer (5 cols) */}
              <div className="md:col-span-5 flex flex-col h-full space-y-4 min-h-[400px]">
                <div className="flex-1 min-h-0">
                  <CodeViewer
                    file={selectedFile}
                    onSetAsTarget={path => {
                      setTargetFile(path);
                      showAlert(`Set '${path}' as diagnosis focus target`, 'info');
                    }}
                    isTarget={targetFile === selectedFile?.file_path}
                  />
                </div>

                {/* Proposed Patch Section */}
                {activePatch && (
                  <div className="h-1/2 min-h-0">
                    <PatchReviewModal
                      patch={activePatch}
                      onApprove={handleApprovePatch}
                      onApply={handleApplyPatch}
                      isApplying={isApplyingPatch}
                    />
                  </div>
                )}
              </div>

              {/* Column 3: Intelligence & Verification (4 cols) */}
              <div className="md:col-span-4 flex flex-col h-full space-y-4 min-h-[400px] overflow-y-auto pr-1">
                {/* 1. Diagnosis Agent */}
                <div className="shrink-0">
                  <BugAnalysisPanel
                    finding={activeFinding}
                    isAnalyzing={isAnalyzing}
                    onAnalyze={handleAnalyzeBug}
                    targetFile={targetFile}
                    onSelectTargetFile={setTargetFile}
                    onGeneratePatch={handleGeneratePatch}
                    isPatchGenerating={isPatchGenerating}
                  />
                </div>

                {/* 2. Regression Test Agent */}
                <div className="shrink-0">
                  <RegressionTestPanel
                    test={activeTest}
                    onGenerateTest={handleGenerateTest}
                    isGenerating={isGeneratingTest}
                    onTriggerVerification={handleRunVerification}
                    isVerifying={isVerifying}
                  />
                </div>

                {/* 3. Verification Engine */}
                <div className="shrink-0">
                  <VerificationTerminal
                    run={activeRun}
                    isRunning={isVerifying}
                    onReverify={handleRunVerification}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Export Report Modal */}
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        reportData={exportData}
      />
    </div>
  );
};
export default App;
