from __future__ import annotations
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class FileNode(BaseModel):
    name: str
    path: str
    type: str  # "file" or "directory"
    size: Optional[int] = 0
    language: Optional[str] = None
    is_test: Optional[bool] = False
    children: Optional[List[FileNode]] = None

class ProjectCreate(BaseModel):
    name: str

class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    created_at: datetime
    file_count: int
    total_size_bytes: int
    languages: List[str]
    manifests: List[str]
    test_frameworks: List[str]


class ProjectDetail(ProjectSummary):
    storage_path: str
    tree: Optional[FileNode] = None

class FileContentResponse(BaseModel):
    project_id: str
    file_path: str
    content: str
    language: str
    size: int
    is_test: bool
