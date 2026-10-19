from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class EvidenceItem(BaseModel):
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: str
    description: str

class BugAnalysisRequest(BaseModel):
    bug_description: str = Field(..., min_length=5, description="Description of the bug, symptoms, or error trace")
    target_file: Optional[str] = Field(None, description="Optional primary file to focus investigation on")
    selected_files: Optional[List[str]] = Field(default_factory=list, description="Optional subset of files")

class BugFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    severity: str
    confidence: float
    suspected_root_cause: str
    explanation: str
    evidence: List[Dict[str, Any]]
    affected_files: List[str]
    created_at: datetime


class SessionCreateRequest(BaseModel):
    project_id: str
    bug_description: Optional[str] = ""
    target_file: Optional[str] = None
