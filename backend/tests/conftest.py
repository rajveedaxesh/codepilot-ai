import os
import io
import zipfile
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.config import settings
from backend.app.db.session import Base, get_db
from backend.app.main import app

from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(test_db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_zip_bytes():
    """Build in-memory sample repo ZIP containing python files and tests."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "src/math_engine.py",
            "def divide(a: float, b: float) -> float:\n    # Bug: missing check for b == 0\n    return a / b\n"
        )
        zf.writestr(
            "tests/test_math.py",
            "import pytest\nfrom src.math_engine import divide\n\ndef test_divide():\n    assert divide(10, 2) == 5\n"
        )
        zf.writestr(
            "pyproject.toml",
            "[project]\nname = 'sample-repo'\nversion = '0.1.0'\n"
        )
    zip_buffer.seek(0)
    return zip_buffer.getvalue()
