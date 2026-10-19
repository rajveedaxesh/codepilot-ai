export interface Project {
  id: string;
  name: string;
  created_at: string;
  file_count: number;
  total_size_bytes: number;
  languages: string[];
  manifests: string[];
  test_frameworks: string[];
}

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  language?: string;
  is_test?: boolean;
  children?: FileNode[];
}

export interface FileContent {
  project_id: string;
  file_path: string;
  content: string;
  language: string;
  size: number;
  is_test: boolean;
}

export interface EvidenceItem {
  file_path: string;
  line_start?: number;
  line_end?: number;
  code_snippet: string;
  description: string;
}

export interface BugFinding {
  id: string;
  session_id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  suspected_root_cause: string;
  explanation: string;
  evidence: EvidenceItem[];
  affected_files: string[];
  created_at: string;
}

export interface ProposedPatch {
  id: string;
  session_id: string;
  diff_content: string;
  affected_files: string[];
  rationale: string;
  status: 'pending' | 'approved' | 'rejected' | 'applied';
  is_approved: boolean;
  is_applied: boolean;
  approved_at?: string;
  created_at: string;
}

export interface RegressionTest {
  id: string;
  session_id: string;
  file_path: string;
  test_code: string;
  test_framework: string;
  test_rationale: string;
  assertion_description: string;
  is_verified: boolean;
  created_at: string;
}

export interface VerificationRun {
  id: string;
  session_id: string;
  command: string;
  exit_code: number;
  duration_ms: number;
  stdout: string;
  stderr: string;
  is_verified: boolean;
  baseline_exit_code?: number;
  baseline_output?: string;
  status: 'verified' | 'unverified' | 'failed' | 'error';
  summary: string;
  created_at: string;
}

export interface AnalysisSession {
  id: string;
  project_id: string;
  project_name?: string;
  status: string;
  bug_description?: string;
  target_file?: string;
  created_at: string;
  updated_at: string;
  findings: BugFinding[];
  patches: ProposedPatch[];
  regression_tests: RegressionTest[];
  verification_runs: VerificationRun[];
}

export interface BenchmarkFixtureResult {
  fixture_id: string;
  name: string;
  category: string;
  file: string;
  localized: boolean;
  valid_patch: boolean;
  test_passed: boolean;
  verified_fix: boolean;
  duration_s: number;
  exit_code: number;
  severity: string;
  confidence: number;
}

export interface BenchmarkSuiteResult {
  timestamp: number;
  provider: string;
  total_fixtures: number;
  localization_accuracy: number;
  valid_patch_rate: number;
  regression_test_pass_rate: number;
  verified_fix_rate: number;
  false_positive_rate: number;
  median_duration_seconds: number;
  estimated_cost_usd: number;
  fixtures: BenchmarkFixtureResult[];
}
