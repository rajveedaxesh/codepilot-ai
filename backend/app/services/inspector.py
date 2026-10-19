import os
import zipfile
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from backend.app.config import settings
from backend.app.services.sanitizer import (
    validate_safe_path, is_safe_file, redact_secrets, SecurityError
)

EXTENSION_LANGUAGE_MAP = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".sh": "shell",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
}

MANIFEST_FILES = {
    "pyproject.toml": "Python (pyproject.toml)",
    "requirements.txt": "Python (requirements.txt)",
    "setup.py": "Python (setup.py)",
    "Pipfile": "Python (Pipfile)",
    "package.json": "JavaScript/TypeScript (package.json)",
    "Cargo.toml": "Rust (Cargo.toml)",
    "go.mod": "Go (go.mod)",
    "pom.xml": "Java (pom.xml)",
    "build.gradle": "Java/Kotlin (Gradle)",
}

TEST_INDICATORS = {
    "pytest": ["pytest.ini", "conftest.py", "test_*.py", "*_test.py"],
    "unittest": ["test_*.py"],
    "jest": ["jest.config.js", "jest.config.ts", "*.test.ts", "*.spec.ts", "*.test.js"],
    "vitest": ["vitest.config.ts", "vitest.config.js"],
}

class SafeExtractionError(Exception):
    pass

def extract_archive_safely(zip_path: Path, target_dir: Path) -> Dict[str, Any]:
    """
    Safely extract a ZIP archive protecting against ZipSlip, bomb archives,
    oversized files, and hidden/dangerous files.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    total_uncompressed_bytes = 0
    extracted_count = 0

    if not zipfile.is_zipfile(zip_path):
        raise SafeExtractionError("Uploaded file is not a valid ZIP archive.")

    with zipfile.ZipFile(zip_path, 'r') as zf:
        infolist = zf.infolist()

        if len(infolist) > settings.MAX_FILE_COUNT:
            raise SafeExtractionError(
                f"Archive contains {len(infolist)} files, exceeding limit of {settings.MAX_FILE_COUNT}."
            )

        for member in infolist:
            # Check uncompressed size
            total_uncompressed_bytes += member.file_size
            if total_uncompressed_bytes > settings.MAX_ARCHIVE_TOTAL_EXTRACT_SIZE:
                raise SafeExtractionError(
                    f"Total uncompressed archive size exceeds limit of {settings.MAX_ARCHIVE_TOTAL_EXTRACT_SIZE / (1024*1024):.0f}MB."
                )

            # ZipSlip Path Traversal Protection
            member_path = Path(member.filename)
            try:
                dest_path = validate_safe_path(target_dir, member.filename)
            except SecurityError as e:
                raise SafeExtractionError(f"ZipSlip security violation in member '{member.filename}': {str(e)}")

            # Check if file is safe
            safe, reason = is_safe_file(member_path)
            if not safe:
                continue

            if member.is_dir():
                dest_path.mkdir(parents=True, exist_ok=True)
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                # Read content safely
                with zf.open(member) as source, open(dest_path, "wb") as target:
                    target.write(source.read())
                extracted_count += 1

    return {
        "extracted_files": extracted_count,
        "total_bytes": total_uncompressed_bytes
    }

def inspect_repository(repo_dir: Path) -> Dict[str, Any]:
    """Inspect repository files, detect languages, manifests, and test frameworks."""
    languages = set()
    manifests = []
    test_frameworks = set()
    file_count = 0
    total_size = 0

    for root, dirs, files in os.walk(repo_dir):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if is_safe_file(Path(d))[0]]
        
        for f in files:
            file_path = Path(root) / f
            rel_path = file_path.relative_to(repo_dir)
            safe, _ = is_safe_file(rel_path)
            if not safe:
                continue

            file_count += 1
            try:
                size = file_path.stat().st_size
                total_size += size
            except OSError:
                size = 0

            # Language detection
            ext = file_path.suffix.lower()
            if ext in EXTENSION_LANGUAGE_MAP:
                languages.add(EXTENSION_LANGUAGE_MAP[ext])

            # Manifest detection
            if f in MANIFEST_FILES:
                manifests.append(MANIFEST_FILES[f])

            # Test framework heuristics
            lower_name = f.lower()
            if lower_name.startswith("test_") or lower_name.endswith("_test.py") or "conftest.py" in lower_name:
                test_frameworks.add("pytest")
            elif ".test." in lower_name or ".spec." in lower_name:
                test_frameworks.add("jest / vitest")

    return {
        "file_count": file_count,
        "total_size_bytes": total_size,
        "languages": sorted(list(languages)),
        "manifests": sorted(manifests),
        "test_frameworks": sorted(list(test_frameworks)) or ["pytest"]
    }

def build_file_tree(repo_dir: Path) -> Dict[str, Any]:
    """Build a recursive directory and file hierarchy for the frontend explorer."""
    def _build_node(path: Path) -> Optional[Dict[str, Any]]:
        rel_path = path.relative_to(repo_dir).as_posix()
        safe, _ = is_safe_file(Path(rel_path)) if rel_path != "." else (True, "")
        if not safe:
            return None

        if path.is_dir():
            children = []
            try:
                entries = sorted(list(path.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
                for entry in entries:
                    child_node = _build_node(entry)
                    if child_node:
                        children.append(child_node)
            except PermissionError:
                pass

            return {
                "name": path.name if rel_path != "." else repo_dir.name,
                "path": rel_path if rel_path != "." else "",
                "type": "directory",
                "size": 0,
                "language": None,
                "is_test": "test" in path.name.lower(),
                "children": children
            }
        else:
            ext = path.suffix.lower()
            lang = EXTENSION_LANGUAGE_MAP.get(ext, "text")
            is_test = "test" in path.name.lower() or path.parent.name.lower() == "tests"
            try:
                size = path.stat().st_size
            except OSError:
                size = 0

            return {
                "name": path.name,
                "path": rel_path,
                "type": "file",
                "size": size,
                "language": lang,
                "is_test": is_test,
                "children": None
            }

    root_tree = _build_node(repo_dir)
    return root_tree or {
        "name": repo_dir.name,
        "path": "",
        "type": "directory",
        "size": 0,
        "children": []
    }

def read_file_safely(repo_dir: Path, rel_path: str) -> Dict[str, Any]:
    """Safely read and redact a source file's contents."""
    safe_path = validate_safe_path(repo_dir, rel_path)
    if not safe_path.is_file():
        raise FileNotFoundError(f"File not found: {rel_path}")

    size = safe_path.stat().st_size
    if size > settings.MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File size exceeds readable limit ({size} > {settings.MAX_FILE_SIZE_BYTES} bytes)")

    try:
        content = safe_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        content = f"Error reading file content: {str(e)}"

    content = redact_secrets(content)
    ext = safe_path.suffix.lower()
    lang = EXTENSION_LANGUAGE_MAP.get(ext, "text")
    is_test = "test" in safe_path.name.lower() or "tests" in safe_path.parts

    return {
        "file_path": rel_path,
        "content": content,
        "language": lang,
        "size": size,
        "is_test": is_test
    }

def find_relevant_code(repo_dir: Path, bug_description: str, target_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Deterministically retrieve relevant code files and test references based on
    the bug description and target file, locating exact line numbers and context.
    """
    snippets = []
    
    # 1. If explicit target_file is provided, read and analyze it first
    if target_file:
        try:
            file_data = read_file_safely(repo_dir, target_file)
            lines = file_data["content"].splitlines()
            snippets.append({
                "file_path": target_file,
                "line_start": 1,
                "line_end": min(len(lines), 100),
                "code_snippet": "\n".join(lines[:100]),
                "description": f"Target file specified for investigation: {target_file}",
                "is_primary": True
            })
        except Exception:
            pass

    # 2. Extract potential search keywords (function names, identifiers, error names)
    keywords = set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{3,}', bug_description))
    # Filter common English stopwords
    stopwords = {"this", "that", "with", "from", "when", "then", "have", "fail", "error", "test", "issue", "bug", "code"}
    keywords = {k.lower() for k in keywords if k.lower() not in stopwords}

    # 3. Deterministically scan repository source files
    for root, dirs, files in os.walk(repo_dir):
        dirs[:] = [d for d in dirs if is_safe_file(Path(d))[0]]
        for f in files:
            file_path = Path(root) / f
            rel_path = file_path.relative_to(repo_dir).as_posix()
            if target_file and rel_path == target_file:
                continue

            safe, _ = is_safe_file(Path(rel_path))
            if not safe or file_path.suffix.lower() not in EXTENSION_LANGUAGE_MAP:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()
                
                # Check for keyword matches
                matching_lines = []
                for idx, line in enumerate(lines, 1):
                    lower_line = line.lower()
                    if any(kw in lower_line for kw in keywords):
                        matching_lines.append((idx, line))

                if matching_lines:
                    first_match_line = matching_lines[0][0]
                    start = max(1, first_match_line - 5)
                    end = min(len(lines), first_match_line + 15)
                    matched_snippet = "\n".join(lines[start-1:end])
                    snippets.append({
                        "file_path": rel_path,
                        "line_start": start,
                        "line_end": end,
                        "code_snippet": matched_snippet,
                        "description": f"Matched keywords in {rel_path} around line {first_match_line}",
                        "is_primary": False
                    })
            except Exception:
                continue

            if len(snippets) >= 5:
                break
        if len(snippets) >= 5:
            break

    # If nothing matched keywords, include the first source file found
    if not snippets:
        for root, dirs, files in os.walk(repo_dir):
            dirs[:] = [d for d in dirs if is_safe_file(Path(d))[0]]
            for f in files:
                file_path = Path(root) / f
                rel_path = file_path.relative_to(repo_dir).as_posix()
                if is_safe_file(Path(rel_path))[0] and file_path.suffix.lower() in {".py", ".ts", ".js"}:
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="replace")
                        lines = content.splitlines()
                        snippets.append({
                            "file_path": rel_path,
                            "line_start": 1,
                            "line_end": min(len(lines), 50),
                            "code_snippet": "\n".join(lines[:50]),
                            "description": f"Repository entry source file: {rel_path}",
                            "is_primary": True
                        })
                        break
                    except Exception:
                        pass
            if snippets:
                break

    return snippets
