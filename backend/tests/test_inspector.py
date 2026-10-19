import io
import zipfile
import tempfile
from pathlib import Path
import pytest

from backend.app.services.inspector import (
    extract_archive_safely, inspect_repository, build_file_tree, read_file_safely, SafeExtractionError
)
from backend.app.services.sanitizer import is_safe_file, redact_secrets, SecurityError, validate_safe_path

def test_safe_extraction_normal(sample_zip_bytes):
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        zip_file = tmp_path / "repo.zip"
        zip_file.write_bytes(sample_zip_bytes)
        
        target_dir = tmp_path / "extracted"
        result = extract_archive_safely(zip_file, target_dir)
        
        assert result["extracted_files"] >= 2
        assert (target_dir / "src" / "math_engine.py").exists()
        assert (target_dir / "pyproject.toml").exists()

def test_zipslip_rejection():
    """Verify that archives with traversal paths (e.g. ../evil.txt) are strictly blocked."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../../evil.txt", "MALICIOUS CONTENT")
    buf.seek(0)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        bad_zip = tmp_path / "bad.zip"
        bad_zip.write_bytes(buf.getvalue())
        target_dir = tmp_path / "dest"

        with pytest.raises(SafeExtractionError) as exc_info:
            extract_archive_safely(bad_zip, target_dir)
        assert "ZipSlip" in str(exc_info.value) or "traversal" in str(exc_info.value).lower()

def test_secret_exclusion():
    safe_rel = Path("src/app.py")
    assert is_safe_file(safe_rel)[0] is True

    env_rel = Path(".env")
    assert is_safe_file(env_rel)[0] is False

    git_rel = Path(".git/config")
    assert is_safe_file(git_rel)[0] is False

    node_rel = Path("node_modules/package/index.js")
    assert is_safe_file(node_rel)[0] is False

    binary_rel = Path("bin/malicious.exe")
    assert is_safe_file(binary_rel)[0] is False

def test_secret_redaction():
    code_with_secret = 'api_key = "sk-ant-api03-abcdef1234567890abcdef123456"'
    redacted = redact_secrets(code_with_secret)
    assert "***REDACTED_API_KEY***" in redacted
    assert "abcdef1234567890" not in redacted

def test_path_traversal_validator():
    base = Path("C:/safe/repo")
    with pytest.raises(SecurityError):
        validate_safe_path(base, "../../../Windows/System32/calc.exe")
