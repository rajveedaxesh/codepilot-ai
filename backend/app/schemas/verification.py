from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class VerificationRunRequest(BaseModel):
    command: Optional[str] = Field(None, description="Test command to run (must match security allowlist)")
    run_baseline: bool = Field(True, description="Whether to verify reproduction failure on original baseline before patch")

class VerificationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    command: str
    exit_code: int
    duration_ms: int
    stdout: str
    stderr: str
    is_verified: bool
    baseline_exit_code: Optional[int] = None
    baseline_output: Optional[str] = None
    status: str  # verified, unverified, failed, error
    summary: str
    created_at: datetime


class SessionFullResponse(BaseModel):
    id: str
    project_id: str
    project_name: Optional[str] = None
    status: str
    bug_description: Optional[str] = None
    target_file: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    findings: List[Dict[str, Any]]
    patches: List[Dict[str, Any]]
    regression_tests: List[Dict[str, Any]]
    verification_runs: List[Dict[str, Any]]
