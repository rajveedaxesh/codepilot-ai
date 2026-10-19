from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models import AnalysisSession, Project, BugFinding, ProposedPatch, RegressionTest, VerificationRun
from backend.app.schemas.analysis import BugAnalysisRequest, BugFindingResponse, SessionCreateRequest
from backend.app.schemas.patch import PatchGenerateRequest, PatchApprovalRequest, ProposedPatchResponse, PatchApplyResponse
from backend.app.schemas.test_schema import RegressionTestGenerateRequest, RegressionTestResponse
from backend.app.schemas.verification import VerificationRunRequest, VerificationRunResponse, SessionFullResponse
from backend.app.schemas.export import SessionExportResponse
from backend.app.services.orchestrator import WorkflowOrchestrator, OrchestrationError

router = APIRouter(prefix="/sessions", tags=["Agent Workflow"])

@router.post("", response_model=Dict[str, Any])
def create_session(request: SessionCreateRequest, db: Session = Depends(get_db)):
    """Create a new bug analysis session for a repository project."""
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    session = AnalysisSession(
        project_id=project.id,
        status="indexed",
        bug_description=request.bug_description or "",
        target_file=request.target_file
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id, "status": session.status, "project_id": session.project_id}

@router.get("", response_model=List[Dict[str, Any]])
def list_sessions(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List recent analysis sessions, optionally filtered by project."""
    query = db.query(AnalysisSession)
    if project_id:
        query = query.filter(AnalysisSession.project_id == project_id)
    sessions = query.order_by(AnalysisSession.created_at.desc()).all()
    
    return [
        {
            "id": s.id,
            "project_id": s.project_id,
            "project_name": s.project.name if s.project else "Unknown",
            "status": s.status,
            "bug_description": s.bug_description or "",
            "target_file": s.target_file,
            "findings_count": len(s.findings),
            "patches_count": len(s.patches),
            "created_at": s.created_at,
            "updated_at": s.updated_at
        }
        for s in sessions
    ]

@router.get("/{session_id}", response_model=SessionFullResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Retrieve complete status, findings, patches, tests, and execution runs for a session."""
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    findings_data = [
        {
            "id": f.id,
            "severity": f.severity,
            "confidence": f.confidence,
            "suspected_root_cause": f.suspected_root_cause,
            "explanation": f.explanation,
            "evidence": f.evidence,
            "affected_files": f.affected_files,
            "created_at": f.created_at
        }
        for f in session.findings
    ]

    patches_data = [
        {
            "id": p.id,
            "diff_content": p.diff_content,
            "affected_files": p.affected_files,
            "rationale": p.rationale,
            "status": p.status,
            "is_approved": p.is_approved,
            "is_applied": p.is_applied,
            "approved_at": p.approved_at,
            "created_at": p.created_at
        }
        for p in session.patches
    ]

    tests_data = [
        {
            "id": t.id,
            "file_path": t.file_path,
            "test_code": t.test_code,
            "test_framework": t.test_framework,
            "test_rationale": t.test_rationale,
            "assertion_description": t.assertion_description,
            "is_verified": t.is_verified,
            "created_at": t.created_at
        }
        for t in session.regression_tests
    ]

    runs_data = [
        {
            "id": r.id,
            "command": r.command,
            "exit_code": r.exit_code,
            "duration_ms": r.duration_ms,
            "stdout": r.stdout,
            "stderr": r.stderr,
            "is_verified": r.is_verified,
            "baseline_exit_code": r.baseline_exit_code,
            "baseline_output": r.baseline_output,
            "status": r.status,
            "summary": r.summary,
            "created_at": r.created_at
        }
        for r in session.verification_runs
    ]

    return SessionFullResponse(
        id=session.id,
        project_id=session.project_id,
        project_name=session.project.name if session.project else None,
        status=session.status,
        bug_description=session.bug_description,
        target_file=session.target_file,
        created_at=session.created_at,
        updated_at=session.updated_at,
        findings=findings_data,
        patches=patches_data,
        regression_tests=tests_data,
        verification_runs=runs_data
    )

@router.post("/{session_id}/analyze", response_model=BugFindingResponse)
def analyze_bug(
    session_id: str,
    request: BugAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Start bug analysis on the session with evidence-backed diagnosis."""
    orchestrator = WorkflowOrchestrator(db)
    try:
        finding = orchestrator.start_bug_analysis(
            session_id=session_id,
            bug_description=request.bug_description,
            target_file=request.target_file
        )
        return finding
    except OrchestrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failure: {str(e)}")

@router.post("/{session_id}/patches", response_model=ProposedPatchResponse)
def generate_patch(
    session_id: str,
    request: Optional[PatchGenerateRequest] = None,
    db: Session = Depends(get_db)
):
    """Generate unified diff patch for a session finding."""
    orchestrator = WorkflowOrchestrator(db)
    finding_id = request.finding_id if request else None
    guidance = request.custom_guidance if request else None
    try:
        patch = orchestrator.generate_patch(session_id, finding_id, guidance)
        return patch
    except OrchestrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Patch generation error: {str(e)}")

@router.post("/{session_id}/patches/{patch_id}/approval", response_model=ProposedPatchResponse)
def approve_or_reject_patch(
    session_id: str,
    patch_id: str,
    request: PatchApprovalRequest,
    db: Session = Depends(get_db)
):
    """Explicitly approve or reject a proposed patch before application."""
    orchestrator = WorkflowOrchestrator(db)
    try:
        patch = orchestrator.process_patch_approval(
            session_id=session_id,
            patch_id=patch_id,
            approved=request.approved,
            rejection_reason=request.rejection_reason
        )
        return patch
    except OrchestrationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{session_id}/patches/{patch_id}/apply", response_model=PatchApplyResponse)
def apply_approved_patch(
    session_id: str,
    patch_id: str,
    db: Session = Depends(get_db)
):
    """Apply an explicitly approved patch to the project."""
    orchestrator = WorkflowOrchestrator(db)
    try:
        modified_files = orchestrator.apply_approved_patch(session_id, patch_id)
        return PatchApplyResponse(
            patch_id=patch_id,
            applied=True,
            modified_files=modified_files,
            message="Patch successfully applied to workspace."
        )
    except OrchestrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Apply error: {str(e)}")

@router.post("/{session_id}/tests", response_model=RegressionTestResponse)
def generate_regression_test(
    session_id: str,
    request: Optional[RegressionTestGenerateRequest] = None,
    db: Session = Depends(get_db)
):
    """Generate a regression test for the reported bug."""
    orchestrator = WorkflowOrchestrator(db)
    patch_id = request.patch_id if request else None
    framework = request.target_framework if request and request.target_framework else "pytest"
    try:
        test = orchestrator.generate_regression_test(session_id, patch_id, framework)
        return test
    except OrchestrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation error: {str(e)}")

@router.post("/{session_id}/verify", response_model=VerificationRunResponse)
def run_verification(
    session_id: str,
    request: Optional[VerificationRunRequest] = None,
    db: Session = Depends(get_db)
):
    """Execute isolated test verification and evaluate genuine fix status."""
    orchestrator = WorkflowOrchestrator(db)
    cmd = request.command if request else None
    run_base = request.run_baseline if request else True
    try:
        run = orchestrator.execute_verification(session_id, cmd, run_base)
        return run
    except OrchestrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification execution error: {str(e)}")

@router.get("/{session_id}/export", response_model=SessionExportResponse)
def export_session_report(session_id: str, db: Session = Depends(get_db)):
    """Export complete diagnosis, patch, and test verification report in Markdown and JSON."""
    orchestrator = WorkflowOrchestrator(db)
    try:
        export_data = orchestrator.generate_export_report(session_id)
        return SessionExportResponse(**export_data)
    except OrchestrationError as e:
        raise HTTPException(status_code=404, detail=str(e))
