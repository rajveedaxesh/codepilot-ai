import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.db.models import (
    Project, AnalysisSession, BugFinding, ProposedPatch, RegressionTest, VerificationRun
)
from backend.app.services.inspector import (
    inspect_repository, find_relevant_code, read_file_safely
)
from backend.app.services.patch_engine import apply_patch, dry_run_patch
from backend.app.services.verifier import run_isolated_verification
from backend.app.ai.factory import get_llm_provider

logger = logging.getLogger(__name__)

class OrchestrationError(Exception):
    pass

class WorkflowOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.llm = get_llm_provider()

    def start_bug_analysis(
        self,
        session_id: str,
        bug_description: str,
        target_file: Optional[str] = None
    ) -> BugFinding:
        """Execute safe bug analysis, populate evidence, and update state."""
        session = self.db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise OrchestrationError(f"Session '{session_id}' not found.")

        project = session.project
        repo_dir = Path(project.storage_path)
        if not repo_dir.exists():
            raise OrchestrationError("Project repository directory is missing.")

        session.status = "analyzing"
        session.bug_description = bug_description
        session.target_file = target_file
        self.db.commit()

        # Gather deterministic code context
        code_context = find_relevant_code(repo_dir, bug_description, target_file)
        repo_info = {
            "languages": project.languages,
            "manifests": project.manifests,
            "test_frameworks": project.test_frameworks,
        }

        # Analyze using LLM provider
        analysis_data = self.llm.analyze_bug(code_context, bug_description, repo_info)

        # Store finding
        finding = BugFinding(
            session_id=session.id,
            severity=analysis_data.get("severity", "medium"),
            confidence=float(analysis_data.get("confidence", 0.85)),
            suspected_root_cause=analysis_data.get("suspected_root_cause", "Unspecified logic flaw"),
            explanation=analysis_data.get("explanation", ""),
            evidence=analysis_data.get("evidence", []),
            affected_files=analysis_data.get("affected_files", [target_file] if target_file else [])
        )
        self.db.add(finding)
        session.status = "analyzed"
        self.db.commit()
        self.db.refresh(finding)
        return finding

    def generate_patch(
        self,
        session_id: str,
        finding_id: Optional[str] = None,
        custom_guidance: Optional[str] = None
    ) -> ProposedPatch:
        """Generate unified diff patch for a session finding."""
        session = self.db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise OrchestrationError(f"Session '{session_id}' not found.")

        finding = None
        if finding_id:
            finding = self.db.query(BugFinding).filter(BugFinding.id == finding_id).first()
        if not finding:
            finding = self.db.query(BugFinding).filter(BugFinding.session_id == session_id).order_by(BugFinding.created_at.desc()).first()

        if not finding:
            raise OrchestrationError("No bug finding found to generate patch for.")

        repo_dir = Path(session.project.storage_path)
        code_context = find_relevant_code(repo_dir, session.bug_description or "", session.target_file)

        finding_dict = {
            "severity": finding.severity,
            "confidence": finding.confidence,
            "suspected_root_cause": finding.suspected_root_cause,
            "affected_files": finding.affected_files,
            "explanation": finding.explanation
        }

        patch_data = self.llm.generate_patch(finding_dict, code_context, custom_guidance)
        diff_content = patch_data.get("diff_content", "")

        # Verify patch targets and dry run
        try:
            dry_run_patch(repo_dir, diff_content)
        except Exception as e:
            logger.warning(f"Dry run note: {e}")

        patch = ProposedPatch(
            session_id=session.id,
            diff_content=diff_content,
            affected_files=patch_data.get("affected_files", finding.affected_files),
            rationale=patch_data.get("rationale", "Proposed patch for reported issue"),
            status="pending",
            is_approved=False,
            is_applied=False
        )
        self.db.add(patch)
        session.status = "patch_ready"
        self.db.commit()
        self.db.refresh(patch)
        return patch

    def process_patch_approval(
        self,
        session_id: str,
        patch_id: str,
        approved: bool,
        rejection_reason: Optional[str] = None
    ) -> ProposedPatch:
        """Handle explicit user approval or rejection of a proposed patch."""
        patch = self.db.query(ProposedPatch).filter(
            ProposedPatch.id == patch_id,
            ProposedPatch.session_id == session_id
        ).first()

        if not patch:
            raise OrchestrationError(f"Patch '{patch_id}' not found for this session.")

        session = patch.session
        if approved:
            patch.is_approved = True
            patch.status = "approved"
            patch.approved_at = datetime.now(timezone.utc)
            session.status = "awaiting_verification"
        else:
            patch.is_approved = False
            patch.status = "rejected"
            session.status = "patch_rejected"

        self.db.commit()
        self.db.refresh(patch)
        return patch

    def apply_approved_patch(self, session_id: str, patch_id: str) -> List[str]:
        """Apply an explicitly approved patch to the repository."""
        patch = self.db.query(ProposedPatch).filter(
            ProposedPatch.id == patch_id,
            ProposedPatch.session_id == session_id
        ).first()

        if not patch:
            raise OrchestrationError(f"Patch '{patch_id}' not found.")
        if not patch.is_approved:
            raise OrchestrationError("Patch cannot be applied without explicit user approval.")

        repo_dir = Path(patch.session.project.storage_path)
        modified_files = apply_patch(repo_dir, patch.diff_content)
        patch.is_applied = True
        patch.status = "applied"
        patch.session.status = "patch_applied"
        self.db.commit()
        return modified_files

    def generate_regression_test(
        self,
        session_id: str,
        patch_id: Optional[str] = None,
        target_framework: str = "pytest"
    ) -> RegressionTest:
        """Generate regression test exercising the bug."""
        session = self.db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise OrchestrationError(f"Session '{session_id}' not found.")

        finding = self.db.query(BugFinding).filter(BugFinding.session_id == session_id).order_by(BugFinding.created_at.desc()).first()
        patch = None
        if patch_id:
            patch = self.db.query(ProposedPatch).filter(ProposedPatch.id == patch_id).first()
        if not patch:
            patch = self.db.query(ProposedPatch).filter(ProposedPatch.session_id == session_id).order_by(ProposedPatch.created_at.desc()).first()

        finding_dict = {
            "suspected_root_cause": finding.suspected_root_cause if finding else session.bug_description,
            "affected_files": finding.affected_files if finding else []
        }
        patch_dict = {
            "diff_content": patch.diff_content if patch else ""
        }

        repo_dir = Path(session.project.storage_path)
        code_context = find_relevant_code(repo_dir, session.bug_description or "", session.target_file)

        test_data = self.llm.generate_regression_test(finding_dict, patch_dict, code_context, target_framework)

        reg_test = RegressionTest(
            session_id=session.id,
            file_path=test_data.get("file_path", "tests/test_regression.py"),
            test_code=test_data.get("test_code", ""),
            test_framework=test_data.get("test_framework", target_framework),
            test_rationale=test_data.get("test_rationale", "Regression test for reported bug"),
            assertion_description=test_data.get("assertion_description", "Asserts expected behavior"),
            is_verified=False  # Generated suggestions are NEVER claimed verified upfront!
        )
        self.db.add(reg_test)
        self.db.commit()
        self.db.refresh(reg_test)
        return reg_test

    def execute_verification(
        self,
        session_id: str,
        command: Optional[str] = None,
        run_baseline: bool = True
    ) -> VerificationRun:
        """
        Run verification in an isolated disposable sandbox.
        Determines genuine verification status and updates test / session state.
        """
        session = self.db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise OrchestrationError(f"Session '{session_id}' not found.")

        repo_dir = Path(session.project.storage_path)

        # Determine verification command
        test_cmd = command
        if not test_cmd:
            frameworks = session.project.test_frameworks or []
            if "pytest" in frameworks:
                test_cmd = "pytest -v"
            elif any("jest" in f or "vitest" in f for f in frameworks):
                test_cmd = "npm test"
            else:
                test_cmd = "pytest -v"

        session.status = "testing"
        self.db.commit()

        # Retrieve patch diff if available (only apply in sandbox if not already applied to repo_dir and not rejected)
        patch = self.db.query(ProposedPatch).filter(
            ProposedPatch.session_id == session_id
        ).order_by(ProposedPatch.created_at.desc()).first()
        patch_diff = patch.diff_content if (patch and patch.status != "rejected" and not patch.is_applied) else None



        # Retrieve regression test if available
        reg_test = self.db.query(RegressionTest).filter(
            RegressionTest.session_id == session_id
        ).order_by(RegressionTest.created_at.desc()).first()
        reg_tuple = (reg_test.file_path, reg_test.test_code) if reg_test else None

        # Run in sandbox
        result = run_isolated_verification(
            repo_dir=repo_dir,
            test_command=test_cmd,
            patch_diff=patch_diff,
            regression_test_file=reg_tuple,
            run_baseline=run_baseline
        )

        # Store VerificationRun record
        v_run = VerificationRun(
            session_id=session.id,
            command=result["command"],
            exit_code=result["exit_code"],
            duration_ms=result["duration_ms"],
            stdout=result["stdout"],
            stderr=result["stderr"],
            is_verified=result["is_verified"],
            baseline_exit_code=result["baseline_exit_code"],
            baseline_output=result["baseline_output"],
            status=result["status"],
            summary=result["summary"]
        )
        self.db.add(v_run)

        # Update regression test verified flag ONLY if genuine pass
        if reg_test and result["is_verified"]:
            reg_test.is_verified = True

        session.status = "verified" if result["is_verified"] else "failed"
        self.db.commit()
        self.db.refresh(v_run)
        return v_run

    def generate_export_report(self, session_id: str) -> Dict[str, Any]:
        """Generate structured markdown and JSON export for the session."""
        session = self.db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise OrchestrationError(f"Session '{session_id}' not found.")

        project = session.project
        findings = session.findings
        patches = session.patches
        tests = session.regression_tests
        runs = session.verification_runs

        lines = [
            f"# CodePilot AI — Autonomous Engineering Report",
            f"**Project**: {project.name}",
            f"**Session ID**: `{session.id}`",
            f"**Status**: `{session.status.upper()}`",
            f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## 1. Problem Description",
            f"> {session.bug_description or 'No bug description provided.'}",
            f"- **Target File**: `{session.target_file or 'Entire repository'}`",
            "",
            "## 2. Diagnosis & Evidence",
        ]

        for idx, f in enumerate(findings, 1):
            lines.append(f"### Finding #{idx}: {f.suspected_root_cause}")
            lines.append(f"- **Severity**: `{f.severity.upper()}` | **Confidence**: `{f.confidence * 100:.1f}%`")
            lines.append(f"- **Explanation**: {f.explanation}")
            lines.append(f"- **Affected Files**: {', '.join(f.affected_files)}")
            lines.append("- **Evidence Snippets**:")
            for ev in (f.evidence or []):
                lines.append(f"  - `{ev.get('file_path')}` (L{ev.get('line_start')}-{ev.get('line_end')}): {ev.get('description')}")
                lines.append(f"    ```\n    {ev.get('code_snippet', '').strip()}\n    ```")

        lines.append("")
        lines.append("## 3. Proposed Fix & Patch Review")
        for idx, p in enumerate(patches, 1):
            lines.append(f"### Patch #{idx} ({p.status.upper()})")
            lines.append(f"- **Rationale**: {p.rationale}")
            lines.append(f"- **Explicit Approval**: `{'Approved' if p.is_approved else 'Pending / Rejected'}`")
            lines.append("```diff")
            lines.append(p.diff_content)
            lines.append("```")

        lines.append("")
        lines.append("## 4. Regression Test Suite")
        for idx, t in enumerate(tests, 1):
            status_text = "VERIFIED (Passed in sandbox)" if t.is_verified else "UNVERIFIED (Generated suggestion only)"
            lines.append(f"### Test #{idx}: `{t.file_path}` [{status_text}]")
            lines.append(f"- **Rationale**: {t.test_rationale}")
            lines.append("```python")
            lines.append(t.test_code)
            lines.append("```")

        lines.append("")
        lines.append("## 5. Verification Engine Execution Results")
        if not runs:
            lines.append("_No verification runs executed yet._")
        for idx, r in enumerate(runs, 1):
            lines.append(f"### Run #{idx}: `{r.command}` [{r.status.upper()}]")
            lines.append(f"- **Exit Code**: `{r.exit_code}` | **Duration**: `{r.duration_ms}ms`")
            lines.append(f"- **Summary**: {r.summary}")
            if r.baseline_exit_code is not None:
                lines.append(f"- **Baseline Reproduction Exit Code**: `{r.baseline_exit_code}`")
            lines.append("#### Standard Output:")
            lines.append("```text")
            lines.append(r.stdout or "(Empty stdout)")
            lines.append("```")
            if r.stderr:
                lines.append("#### Standard Error:")
                lines.append("```text")
                lines.append(r.stderr)
                lines.append("```")

        md_report = "\n".join(lines)
        return {
            "session_id": session.id,
            "project_name": project.name,
            "status": session.status,
            "created_at": session.created_at,
            "bug_description": session.bug_description or "",
            "findings": [
                {
                    "id": f.id,
                    "severity": f.severity,
                    "confidence": f.confidence,
                    "suspected_root_cause": f.suspected_root_cause,
                    "explanation": f.explanation,
                    "evidence": f.evidence,
                    "affected_files": f.affected_files
                } for f in findings
            ],
            "patches": [
                {
                    "id": p.id,
                    "diff_content": p.diff_content,
                    "affected_files": p.affected_files,
                    "rationale": p.rationale,
                    "status": p.status,
                    "is_approved": p.is_approved,
                    "is_applied": p.is_applied
                } for p in patches
            ],
            "regression_tests": [
                {
                    "id": t.id,
                    "file_path": t.file_path,
                    "test_code": t.test_code,
                    "test_framework": t.test_framework,
                    "test_rationale": t.test_rationale,
                    "is_verified": t.is_verified
                } for t in tests
            ],
            "verification_runs": [
                {
                    "id": r.id,
                    "command": r.command,
                    "exit_code": r.exit_code,
                    "duration_ms": r.duration_ms,
                    "stdout": r.stdout,
                    "stderr": r.stderr,
                    "is_verified": r.is_verified,
                    "status": r.status,
                    "summary": r.summary
                } for r in runs
            ],
            "markdown_report": md_report,
            "json_data": {
                "session_id": session.id,
                "project_name": project.name,
                "status": session.status,
                "created_at": session.created_at.isoformat()
            }
        }
