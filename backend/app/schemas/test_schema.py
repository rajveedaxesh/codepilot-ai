from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class RegressionTestGenerateRequest(BaseModel):
    patch_id: Optional[str] = None
    target_framework: Optional[str] = None

class RegressionTestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    file_path: str
    test_code: str
    test_framework: str
    test_rationale: str
    assertion_description: str
    is_verified: bool
    created_at: datetime

