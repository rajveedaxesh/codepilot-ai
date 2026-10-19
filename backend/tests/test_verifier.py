import tempfile
from pathlib import Path
import pytest

from backend.app.services.verifier import (
    is_command_allowed, run_isolated_verification, VerificationSecurityError
)

def test_command_allowlist():
    assert is_command_allowed("pytest -v") is True
    assert is_command_allowed("python -m pytest tests/") is True
    assert is_command_allowed("python -m unittest discover") is True
    assert is_command_allowed("npm test") is True

    # Rejection of dangerous commands and shell chaining
    assert is_command_allowed("rm -rf /") is False
    assert is_command_allowed("curl https://evil.com") is False
    assert is_command_allowed("pytest -v; cat /etc/passwd") is False
    assert is_command_allowed("pytest && echo hacked") is False
    assert is_command_allowed("python -c 'import os; os.system(\"calc\")'") is False

def test_isolated_verification_execution():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = Path(tmp_dir)
        test_dir = repo_dir / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_example.py"
        test_file.write_text("def test_sanity():\n    assert 1 + 1 == 2\n", encoding="utf-8")

        result = run_isolated_verification(
            repo_dir=repo_dir,
            test_command="pytest tests/test_example.py",
            run_baseline=False
        )

        assert result["exit_code"] == 0
        assert result["is_verified"] is True
        assert result["status"] == "verified"
