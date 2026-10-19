import os
import re
from pathlib import Path
from typing import List, Tuple
from fastapi import HTTPException
from backend.app.config import settings

SECRET_PATTERNS = [
    # Anthropic / OpenAI / General API Keys
    (re.compile(r'(?i)(?:api[_-]?key|anthropic[_-]?api[_-]?key|openai[_-]?api[_-]?key|secret[_-]?key|access[_-]?token)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{16,})["\']?'), r'***REDACTED_API_KEY***'),
    # Bearer tokens
    (re.compile(r'(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}'), 'Bearer ***REDACTED_TOKEN***'),
    # AWS Access Key IDs
    (re.compile(r'(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])'), '***REDACTED_AWS_KEY***'),
    # Private Key blocks
    (re.compile(r'-----BEGIN [A-Z ]+PRIVATE KEY-----[^-]+-----END [A-Z ]+PRIVATE KEY-----', re.DOTALL), '***REDACTED_PRIVATE_KEY***'),
    # Password variables
    (re.compile(r'(?i)(?:password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^"\'\s]{6,})["\']?'), r'password="***REDACTED_PASSWORD***"'),
]

DANGEROUS_FILE_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".pyc", ".pyd", ".iso", ".msi", ".dmg"
}

SECRET_FILENAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"
}

IGNORED_DIRECTORIES = {
    ".git", ".svn", ".hg", "node_modules", "venv", ".venv", "env",
    "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    ".idea", ".vscode", "dist", "build", ".next", "out"
}

class SecurityError(Exception):
    pass

def redact_secrets(content: str) -> str:
    """Redact known secret patterns from code, logs, and outputs."""
    if not content:
        return ""
    sanitized = content
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized

def validate_safe_path(base_dir: Path, requested_path: str) -> Path:
    """
    Ensure requested relative or absolute path is strictly confined inside base_dir.
    Rejects path traversal (e.g. '../', symlinks escaping base_dir).
    """
    clean_requested = requested_path.strip().lstrip("/\\")
    resolved_base = base_dir.resolve()
    target_path = (resolved_base / clean_requested).resolve()

    try:
        # Check commonpath to ensure target_path is within resolved_base
        common = Path(os.path.commonpath([resolved_base, target_path]))
        if common != resolved_base:
            raise SecurityError(f"Path traversal detected: {requested_path}")
    except ValueError:
        raise SecurityError(f"Invalid path traversal attempt: {requested_path}")

    return target_path

def is_safe_file(rel_path: Path) -> Tuple[bool, str]:
    """Check if file should be included or rejected."""
    parts = rel_path.parts
    for part in parts:
        if part in IGNORED_DIRECTORIES:
            return False, f"Ignored directory: {part}"
        if part.startswith(".") and part != ".":
            # Hidden dot directories or files
            if part in SECRET_FILENAMES or "env" in part.lower():
                return False, f"Sensitive hidden file/folder: {part}"

    filename = rel_path.name
    if filename in SECRET_FILENAMES:
        return False, f"Sensitive secret file: {filename}"

    ext = rel_path.suffix.lower()
    if ext in DANGEROUS_FILE_EXTENSIONS:
        return False, f"Dangerous/binary extension: {ext}"

    return True, "Safe"
