import os
import sys
import time
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List

from backend.app.config import settings
from backend.app.services.sanitizer import redact_secrets

class VerificationSecurityError(Exception):
    pass

def sanitize_environment() -> Dict[str, str]:
    """Provide a minimal, safe environment for test execution without leaking host secrets."""
    safe_keys = ["PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LOCALAPPDATA", "LANG", "LC_ALL"]
    safe_env = {k: os.environ[k] for k in safe_keys if k in os.environ}
    # Add python path
    safe_env["PYTHONUNBUFFERED"] = "1"
    safe_env["PYTHONDONTWRITEBYTECODE"] = "1"
    return safe_env

def is_command_allowed(command: str) -> bool:
    """Strictly validate command against security allowlist and forbid shell chaining."""
    clean_cmd = command.strip()
    
    # Check for forbidden shell metacharacters
    forbidden_tokens = [";", "&&", "||", "|", "&", ">", "<", "`", "$", "\n", "\r"]
    for token in forbidden_tokens:
        if token in clean_cmd:
            return False

    # Check prefix allowlist
    allowed = any(clean_cmd.startswith(prefix) for prefix in settings.ALLOWED_COMMAND_PREFIXES)
    return allowed

def execute_sandboxed_command(
    workspace_dir: Path,
    command: str,
    timeout_seconds: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute an allowed test command inside a designated workspace directory.
    Captures duration, exit code, stdout, and stderr.
    """
    if not is_command_allowed(command):
        raise VerificationSecurityError(
            f"Command '{command}' is not in the security allowlist or contains forbidden shell operators."
        )

    timeout = timeout_seconds or settings.EXECUTION_TIMEOUT_SECONDS
    env = sanitize_environment()
    
    # Resolve 'python' and 'pytest' to current virtualenv interpreter if available
    cmd_parts = command.split()
    if cmd_parts[0] == "python":
        cmd_parts[0] = sys.executable
    elif cmd_parts[0] == "pytest":
        # Run via current python -m pytest to ensure module resolution
        cmd_parts = [sys.executable, "-m", "pytest"] + cmd_parts[1:]

    start_time = time.perf_counter()
    try:
        process = subprocess.run(
            cmd_parts,
            cwd=str(workspace_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False  # Crucial: shell=False prevents shell injection attacks
        )
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "exit_code": process.returncode,
            "stdout": redact_secrets(process.stdout),
            "stderr": redact_secrets(process.stderr),
            "duration_ms": duration_ms,
            "timed_out": False
        }
    except subprocess.TimeoutExpired as e:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "exit_code": -1,
            "stdout": redact_secrets(e.stdout or ""),
            "stderr": f"Execution timed out after {timeout} seconds.",
            "duration_ms": duration_ms,
            "timed_out": True
        }
    except Exception as e:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Execution error: {str(e)}",
            "duration_ms": duration_ms,
            "timed_out": False
        }

def run_isolated_verification(
    repo_dir: Path,
    test_command: str,
    patch_diff: Optional[str] = None,
    regression_test_file: Optional[Tuple[str, str]] = None, # (rel_path, code)
    run_baseline: bool = True
) -> Dict[str, Any]:
    """
    Creates a disposable workspace, optionally executes baseline reproduction,
    applies the patch and regression test, executes verification, and evaluates fix status.
    """
    run_id = uuid.uuid4().hex[:12]
    temp_sandbox = settings.SANDBOX_DIR / f"run_{run_id}"

    baseline_result = None
    try:
        # Create disposable copy of the repo
        shutil.copytree(repo_dir, temp_sandbox, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))

        # 1. Baseline reproduction run (if requested)
        if run_baseline:
            # If a regression test is supplied, write it to the baseline to check reproduction
            if regression_test_file:
                test_path = temp_sandbox / regression_test_file[0]
                test_path.parent.mkdir(parents=True, exist_ok=True)
                test_path.write_text(regression_test_file[1], encoding="utf-8")

            baseline_result = execute_sandboxed_command(temp_sandbox, test_command)

        # 2. Apply patch in sandbox
        if patch_diff:
            from backend.app.services.patch_engine import apply_patch
            apply_patch(temp_sandbox, patch_diff)

        # Ensure regression test is in place on patched workspace
        if regression_test_file:
            test_path = temp_sandbox / regression_test_file[0]
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(regression_test_file[1], encoding="utf-8")

        # 3. Verification run on patched code
        patched_result = execute_sandboxed_command(temp_sandbox, test_command)

        # 4. Determine genuine verification status
        # A fix is verified ONLY if patched tests exit 0.
        exit_code = patched_result["exit_code"]
        is_verified = (exit_code == 0)

        if is_verified:
            if baseline_result and baseline_result["exit_code"] != 0:
                summary = "Fix Verified: Bug successfully reproduced on baseline and resolved on patched code."
                status = "verified"
            else:
                summary = "Tests Passed: Verification command exited cleanly with code 0 on patched code."
                status = "verified"
        else:
            if patched_result["timed_out"]:
                summary = f"Verification Failed: Execution timed out after {settings.EXECUTION_TIMEOUT_SECONDS}s."
                status = "unverified"
            else:
                summary = f"Verification Failed: Tests exited with non-zero code {exit_code}."
                status = "failed"

        return {
            "command": test_command,
            "exit_code": exit_code,
            "duration_ms": patched_result["duration_ms"],
            "stdout": patched_result["stdout"],
            "stderr": patched_result["stderr"],
            "is_verified": is_verified,
            "baseline_exit_code": baseline_result["exit_code"] if baseline_result else None,
            "baseline_output": baseline_result["stdout"] if baseline_result else None,
            "status": status,
            "summary": summary
        }

    finally:
        # Clean up disposable sandbox
        if temp_sandbox.exists():
            shutil.rmtree(temp_sandbox, ignore_errors=True)
