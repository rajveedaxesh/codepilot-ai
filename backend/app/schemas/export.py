from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class SessionExportResponse(BaseModel):
    session_id: str
    project_name: str
    status: str
    created_at: datetime
    bug_description: str
    findings: List[Dict[str, Any]]
    patches: List[Dict[str, Any]]
    regression_tests: List[Dict[str, Any]]
    verification_runs: List[Dict[str, Any]]
    markdown_report: str
    json_data: Dict[str, Any]
