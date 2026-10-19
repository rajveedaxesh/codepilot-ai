from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class PatchGenerateRequest(BaseModel):
    finding_id: Optional[str] = None
    custom_guidance: Optional[str] = None

class PatchApprovalRequest(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None

class ProposedPatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    diff_content: str
    affected_files: List[str]
    rationale: str
    status: str
    is_approved: bool
    is_applied: bool
    approved_at: Optional[datetime] = None
    created_at: datetime


class PatchApplyResponse(BaseModel):
    patch_id: str
    applied: bool
    modified_files: List[str]
    message: str
