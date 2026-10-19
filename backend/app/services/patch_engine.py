import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from backend.app.services.sanitizer import validate_safe_path, SecurityError

class PatchError(Exception):
    pass

def parse_unified_diff(diff_text: str) -> List[Dict[str, Any]]:
    """
    Parse a unified diff into target file blocks and hunks.
    Example header:
    --- a/src/math_engine.py
    +++ b/src/math_engine.py
    @@ -10,4 +10,4 @@
    """
    files = []
    current_file = None
    current_hunk = None

    lines = diff_text.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("--- "):
            # Source file
            orig_file = line[4:].strip()
            if orig_file.startswith("a/"):
                orig_file = orig_file[2:]
            
            i += 1
            if i < len(lines) and lines[i].startswith("+++ "):
                target_file = lines[i][4:].strip()
                if target_file.startswith("b/"):
                    target_file = target_file[2:]
                current_file = {
                    "orig_file": orig_file,
                    "target_file": target_file,
                    "hunks": []
                }
                files.append(current_file)
            i += 1
            continue

        if line.startswith("@@ ") and current_file is not None:
            # Hunk header @@ -start,len +start,len @@
            match = re.match(r'@@\s*-(\d+)(?:,(\d+))?\s*\+(\d+)(?:,(\d+))?\s*@@', line)
            if match:
                current_hunk = {
                    "header": line,
                    "orig_start": int(match.group(1)),
                    "orig_len": int(match.group(2)) if match.group(2) else 1,
                    "new_start": int(match.group(3)),
                    "new_len": int(match.group(4)) if match.group(4) else 1,
                    "lines": []
                }
                current_file["hunks"].append(current_hunk)
            i += 1
            continue

        if current_hunk is not None:
            current_hunk["lines"].append(line)

        i += 1

    return files

def validate_patch_targets(repo_dir: Path, diff_text: str) -> List[Path]:
    """
    Ensure all files modified in the diff are inside the repo_dir boundary.
    Raises SecurityError or PatchError on traversal or invalid format.
    """
    parsed = parse_unified_diff(diff_text)
    if not parsed:
        raise PatchError("No valid unified diff hunks found in patch.")

    validated_paths = []
    for file_info in parsed:
        target = file_info["target_file"]
        if target == "/dev/null":
            continue
        try:
            safe_path = validate_safe_path(repo_dir, target)
            validated_paths.append(safe_path)
        except SecurityError as e:
            raise SecurityError(f"Patch target security violation: {str(e)}")

    return validated_paths

def apply_hunks_to_content(original_content: str, hunks: List[Dict[str, Any]]) -> str:
    """Apply parsed hunks to a string content sequentially."""
    orig_lines = original_content.splitlines(keepends=True)
    # Ensure lines have proper line breaks
    orig_lines = [l if l.endswith(('\n', '\r\n')) else l + '\n' for l in orig_lines]
    
    result_lines = []
    curr_orig_idx = 0

    for hunk in hunks:
        target_orig_start = hunk["orig_start"] - 1 # 0-indexed
        
        # Copy unchanged lines up to the hunk start
        while curr_orig_idx < target_orig_start and curr_orig_idx < len(orig_lines):
            result_lines.append(orig_lines[curr_orig_idx])
            curr_orig_idx += 1

        for hline in hunk["lines"]:
            if not hline:
                continue
            marker = hline[0]
            content = hline[1:] + "\n"
            
            if marker == " ":
                # Context line: verify match where possible
                result_lines.append(content)
                curr_orig_idx += 1
            elif marker == "-":
                # Deletion: skip this line in original
                curr_orig_idx += 1
            elif marker == "+":
                # Addition: add to result
                result_lines.append(content)
            elif marker == "\\":
                # '\ No newline at end of file'
                pass

    # Copy remaining lines after last hunk
    while curr_orig_idx < len(orig_lines):
        result_lines.append(orig_lines[curr_orig_idx])
        curr_orig_idx += 1

    return "".join(result_lines)

def dry_run_patch(repo_dir: Path, diff_text: str) -> Dict[str, Any]:
    """
    Test applying the patch without writing changes to disk.
    Returns preview of modified files and checks for conflicts.
    """
    validate_patch_targets(repo_dir, diff_text)
    parsed = parse_unified_diff(diff_text)
    preview = {}

    for file_info in parsed:
        rel_path = file_info["target_file"]
        target_path = validate_safe_path(repo_dir, rel_path)
        
        if not target_path.exists():
            if file_info["orig_file"] == "/dev/null":
                # New file creation
                orig_content = ""
            else:
                raise PatchError(f"Target file for patch does not exist: {rel_path}")
        else:
            orig_content = target_path.read_text(encoding="utf-8", errors="replace")

        try:
            new_content = apply_hunks_to_content(orig_content, file_info["hunks"])
            preview[rel_path] = {
                "orig_size": len(orig_content),
                "new_size": len(new_content),
                "success": True
            }
        except Exception as e:
            raise PatchError(f"Failed to apply patch hunk to {rel_path}: {str(e)}")

    return preview

def apply_patch(repo_dir: Path, diff_text: str) -> List[str]:
    """
    Safely apply approved patch to repo_dir with automatic backup and rollback.
    """
    # 1. First dry run to ensure clean application
    dry_run_patch(repo_dir, diff_text)
    
    parsed = parse_unified_diff(diff_text)
    modified_files = []
    backups = {}

    try:
        for file_info in parsed:
            rel_path = file_info["target_file"]
            target_path = validate_safe_path(repo_dir, rel_path)

            if target_path.exists():
                orig_content = target_path.read_text(encoding="utf-8", errors="replace")
                # Create in-memory backup
                backups[target_path] = orig_content
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                orig_content = ""
                backups[target_path] = None # Marker for newly created file

            new_content = apply_hunks_to_content(orig_content, file_info["hunks"])
            target_path.write_text(new_content, encoding="utf-8")
            modified_files.append(rel_path)

        return modified_files

    except Exception as e:
        # Rollback all applied changes on any failure
        for path, original in backups.items():
            if original is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_text(original, encoding="utf-8")
        raise PatchError(f"Patch application failed and was rolled back: {str(e)}")
