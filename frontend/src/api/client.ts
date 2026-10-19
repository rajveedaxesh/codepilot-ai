import type {
  Project, FileNode, FileContent, AnalysisSession, BugFinding,
  ProposedPatch, RegressionTest, VerificationRun, BenchmarkSuiteResult
} from '../types';

const API_BASE = '/api/v1';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) {
        errorMessage = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

export const api = {
  // Health & Settings
  getHealth: () => request<{ status: string; app_name: string; llm_provider: string; anthropic_configured: boolean; sandboxing_enabled: boolean }>('/health'),
  getSettings: () => request<any>('/settings'),

  // Projects
  uploadRepository: (file: File, projectName?: string): Promise<Project> => {
    const formData = new FormData();
    formData.append('file', file);
    if (projectName) {
      formData.append('project_name', projectName);
    }
    return request<Project>('/projects/upload', {
      method: 'POST',
      body: formData,
    });
  },

  loadDemoProject: (): Promise<Project> => {
    return request<Project>('/projects/demo', { method: 'POST' });
  },

  getProjects: (): Promise<Project[]> => {
    return request<Project[]>('/projects');
  },

  getProject: (id: string): Promise<Project> => {
    return request<Project>(`/projects/${id}`);
  },

  getProjectTree: (id: string): Promise<FileNode> => {
    return request<FileNode>(`/projects/${id}/tree`);
  },

  getFileContent: (projectId: string, path: string): Promise<FileContent> => {
    return request<FileContent>(`/projects/${projectId}/file?path=${encodeURIComponent(path)}`);
  },

  // Sessions & Workflow
  createSession: (projectId: string, bugDescription?: string, targetFile?: string): Promise<{ session_id: string; status: string; project_id: string }> => {
    return request('/sessions', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, bug_description: bugDescription, target_file: targetFile }),
    });
  },

  getSessions: (projectId?: string): Promise<any[]> => {
    const q = projectId ? `?project_id=${projectId}` : '';
    return request(`/sessions${q}`);
  },

  getSession: (sessionId: string): Promise<AnalysisSession> => {
    return request<AnalysisSession>(`/sessions/${sessionId}`);
  },

  analyzeBug: (sessionId: string, bugDescription: string, targetFile?: string): Promise<BugFinding> => {
    return request<BugFinding>(`/sessions/${sessionId}/analyze`, {
      method: 'POST',
      body: JSON.stringify({ bug_description: bugDescription, target_file: targetFile }),
    });
  },

  generatePatch: (sessionId: string, findingId?: string, guidance?: string): Promise<ProposedPatch> => {
    return request<ProposedPatch>(`/sessions/${sessionId}/patches`, {
      method: 'POST',
      body: JSON.stringify({ finding_id: findingId, custom_guidance: guidance }),
    });
  },

  approvePatch: (sessionId: string, patchId: string, approved: boolean, rejectionReason?: string): Promise<ProposedPatch> => {
    return request<ProposedPatch>(`/sessions/${sessionId}/patches/${patchId}/approval`, {
      method: 'POST',
      body: JSON.stringify({ approved, rejection_reason: rejectionReason }),
    });
  },

  applyPatch: (sessionId: string, patchId: string): Promise<{ patch_id: string; applied: boolean; modified_files: string[]; message: string }> => {
    return request(`/sessions/${sessionId}/patches/${patchId}/apply`, {
      method: 'POST',
    });
  },

  generateRegressionTest: (sessionId: string, patchId?: string, targetFramework?: string): Promise<RegressionTest> => {
    return request<RegressionTest>(`/sessions/${sessionId}/tests`, {
      method: 'POST',
      body: JSON.stringify({ patch_id: patchId, target_framework: targetFramework }),
    });
  },

  runVerification: (sessionId: string, command?: string, runBaseline = true): Promise<VerificationRun> => {
    return request<VerificationRun>(`/sessions/${sessionId}/verify`, {
      method: 'POST',
      body: JSON.stringify({ command, run_baseline: runBaseline }),
    });
  },

  exportSessionReport: (sessionId: string): Promise<{
    session_id: string;
    project_name: string;
    status: string;
    markdown_report: string;
    json_data: any;
  }> => {
    return request(`/sessions/${sessionId}/export`);
  },

  // Benchmarks
  getBenchmarkFixtures: (): Promise<any[]> => {
    return request('/benchmarks/fixtures');
  },

  runBenchmarkSuite: (): Promise<BenchmarkSuiteResult> => {
    return request<BenchmarkSuiteResult>('/benchmarks/run', {
      method: 'POST',
    });
  },
};
