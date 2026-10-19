import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now)
    storage_path = Column(String(1024), nullable=False)
    file_count = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    languages = Column(JSON, default=list)
    manifests = Column(JSON, default=list)
    test_frameworks = Column(JSON, default=list)

    sessions = relationship("AnalysisSession", back_populates="project", cascade="all, delete-orphan")

class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    status = Column(String(50), default="uploaded", nullable=False)
    bug_description = Column(Text, nullable=True)
    target_file = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="sessions")
    findings = relationship("BugFinding", back_populates="session", cascade="all, delete-orphan")
    patches = relationship("ProposedPatch", back_populates="session", cascade="all, delete-orphan")
    regression_tests = relationship("RegressionTest", back_populates="session", cascade="all, delete-orphan")
    verification_runs = relationship("VerificationRun", back_populates="session", cascade="all, delete-orphan")

class BugFinding(Base):
    __tablename__ = "bug_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("analysis_sessions.id"), nullable=False)
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    confidence = Column(Float, default=0.85)          # 0.0 to 1.0
    suspected_root_cause = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    evidence = Column(JSON, default=list)             # List of snippets / file:line references
    affected_files = Column(JSON, default=list)       # List of relative paths
    created_at = Column(DateTime, default=utc_now)

    session = relationship("AnalysisSession", back_populates="findings")

class ProposedPatch(Base):
    __tablename__ = "proposed_patches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("analysis_sessions.id"), nullable=False)
    diff_content = Column(Text, nullable=False)
    affected_files = Column(JSON, default=list)
    rationale = Column(Text, nullable=False)
    status = Column(String(30), default="pending")    # pending, approved, rejected, applied
    is_approved = Column(Boolean, default=False)
    is_applied = Column(Boolean, default=False)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    session = relationship("AnalysisSession", back_populates="patches")

class RegressionTest(Base):
    __tablename__ = "regression_tests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("analysis_sessions.id"), nullable=False)
    file_path = Column(String(512), nullable=False)
    test_code = Column(Text, nullable=False)
    test_framework = Column(String(50), default="pytest")
    test_rationale = Column(Text, nullable=False)
    assertion_description = Column(Text, nullable=False)
    is_verified = Column(Boolean, default=False)       # Never set to true until genuine test pass
    created_at = Column(DateTime, default=utc_now)

    session = relationship("AnalysisSession", back_populates="regression_tests")

class VerificationRun(Base):
    __tablename__ = "verification_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("analysis_sessions.id"), nullable=False)
    command = Column(String(512), nullable=False)
    exit_code = Column(Integer, nullable=False)
    duration_ms = Column(Integer, default=0)
    stdout = Column(Text, default="")
    stderr = Column(Text, default="")
    is_verified = Column(Boolean, default=False)
    baseline_exit_code = Column(Integer, nullable=True)
    baseline_output = Column(Text, nullable=True)
    status = Column(String(30), default="unverified")  # verified, unverified, failed, error
    summary = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now)

    session = relationship("AnalysisSession", back_populates="verification_runs")
