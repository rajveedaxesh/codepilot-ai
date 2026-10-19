import shutil
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.db.session import get_db
from backend.app.db.models import Project, AnalysisSession
from backend.app.schemas.project import (
    ProjectSummary, ProjectDetail, FileContentResponse, FileNode
)
from backend.app.services.inspector import (
    extract_archive_safely, inspect_repository, build_file_tree, read_file_safely, SafeExtractionError
)
from backend.app.services.sanitizer import SecurityError

router = APIRouter(prefix="/projects", tags=["Repository Intelligence"])

@router.post("/upload", response_model=ProjectSummary)
async def upload_repository_zip(
    file: UploadFile = File(...),
    project_name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Safely upload and inspect a source repository ZIP.
    Protects against ZipSlip, bomb archives, and excluded files.
    """
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip repository archives are supported.")

    project_id = str(uuid.uuid4())
    resolved_name = project_name or Path(file.filename).stem or f"project_{project_id[:8]}"
    project_dir = settings.REPOS_DIR / project_id

    # Stream archive to a secure temporary file first
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
        tmp_zip_path = Path(tmp_zip.name)
        total_uploaded = 0
        while content := await file.read(1024 * 1024):  # 1MB chunks
            total_uploaded += len(content)
            if total_uploaded > settings.MAX_UPLOAD_SIZE_BYTES:
                tmp_zip_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"Upload exceeds maximum allowable limit of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024):.0f}MB."
                )
            tmp_zip.write(content)

    try:
        # Extract safely with ZipSlip protection
        extract_archive_safely(tmp_zip_path, project_dir)
        
        # If the zip has a single root directory inside it, use that directory
        children = [p for p in project_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
        single_root = children[0] if len(children) == 1 and len(list(project_dir.glob("*"))) == 1 else project_dir

        # Inspect repository
        inspection = inspect_repository(single_root)

        # Store in database
        project = Project(
            id=project_id,
            name=resolved_name,
            storage_path=str(single_root),
            file_count=inspection["file_count"],
            total_size_bytes=inspection["total_size_bytes"],
            languages=inspection["languages"],
            manifests=inspection["manifests"],
            test_frameworks=inspection["test_frameworks"],
        )
        db.add(project)

        # Automatically create initial analysis session
        initial_session = AnalysisSession(
            project_id=project.id,
            status="indexed"
        )
        db.add(initial_session)
        db.commit()
        db.refresh(project)

        return project

    except SafeExtractionError as e:
        if project_dir.exists():
            shutil.rmtree(project_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"Archive validation failure: {str(e)}")
    except Exception as e:
        if project_dir.exists():
            shutil.rmtree(project_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Repository inspection error: {str(e)}")
    finally:
        if tmp_zip_path.exists():
            tmp_zip_path.unlink(missing_ok=True)

@router.post("/demo", response_model=ProjectSummary)
def load_demo_project(db: Session = Depends(get_db)):
    """Convenience endpoint: Instantly loads and inspects the built-in sample demo repository."""
    sample_zip = settings.BASE_DIR.parent / "sample_repo.zip"
    if not sample_zip.exists():
        from scripts.pack_sample_repo import create_sample_zip
        create_sample_zip()

    project_id = str(uuid.uuid4())
    project_dir = settings.REPOS_DIR / project_id
    extract_archive_safely(sample_zip, project_dir)

    inspection = inspect_repository(project_dir)
    project = Project(
        id=project_id,
        name="Demo Math & Utility Service",
        storage_path=str(project_dir),
        file_count=inspection["file_count"],
        total_size_bytes=inspection["total_size_bytes"],
        languages=inspection["languages"],
        manifests=inspection["manifests"],
        test_frameworks=inspection["test_frameworks"],
    )
    db.add(project)

    initial_session = AnalysisSession(
        project_id=project.id,
        status="indexed",
        bug_description="ZeroDivisionError when denominator is zero in divide() function",
        target_file="src/math_engine.py"
    )
    db.add(initial_session)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=List[ProjectSummary])
def list_projects(db: Session = Depends(get_db)):
    """List all inspected repositories."""
    return db.query(Project).order_by(Project.created_at.desc()).all()

@router.get("/{project_id}", response_model=ProjectSummary)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific repository project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project

@router.get("/{project_id}/tree")
def get_project_file_tree(project_id: str, db: Session = Depends(get_db)):
    """Retrieve full sanitized file tree for repository exploration."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    repo_dir = Path(project.storage_path)
    if not repo_dir.exists():
        raise HTTPException(status_code=404, detail="Repository files missing on disk.")

    tree = build_file_tree(repo_dir)
    return tree

@router.get("/{project_id}/file", response_model=FileContentResponse)
def get_project_file(
    project_id: str,
    path: str = Query(..., description="Relative file path inside repository"),
    db: Session = Depends(get_db)
):
    """Safely fetch file contents with line limits and secret redaction."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    repo_dir = Path(project.storage_path)
    try:
        file_info = read_file_safely(repo_dir, path)
        return FileContentResponse(
            project_id=project.id,
            file_path=file_info["file_path"],
            content=file_info["content"],
            language=file_info["language"],
            size=file_info["size"],
            is_test=file_info["is_test"]
        )
    except SecurityError as e:
        raise HTTPException(status_code=403, detail=f"Path forbidden: {str(e)}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Read error: {str(e)}")
