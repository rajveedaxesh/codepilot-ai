import tempfile
from pathlib import Path
import pytest

from backend.app.services.patch_engine import (
    parse_unified_diff, validate_patch_targets, apply_patch, dry_run_patch, PatchError
)
from backend.app.services.sanitizer import SecurityError

def test_parse_unified_diff():
    diff_text = """--- a/src/math.py
+++ b/src/math.py
@@ -1,3 +1,5 @@
 def add(a, b):
+    if a is None:
+        return b
     return a + b
"""
    parsed = parse_unified_diff(diff_text)
    assert len(parsed) == 1
    assert parsed[0]["target_file"] == "src/math.py"
    assert len(parsed[0]["hunks"]) == 1

def test_reject_patch_traversal():
    diff_text = """--- a/../../etc/passwd
+++ b/../../etc/passwd
@@ -1,1 +1,1 @@
-root
+hacked
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = Path(tmp_dir)
        with pytest.raises(SecurityError):
            validate_patch_targets(repo_dir, diff_text)

def test_safe_patch_application():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = Path(tmp_dir)
        src_dir = repo_dir / "src"
        src_dir.mkdir()
        file_path = src_dir / "calc.py"
        file_path.write_text("def div(a, b):\n    return a / b\n", encoding="utf-8")

        diff = """--- a/src/calc.py
+++ b/src/calc.py
@@ -1,2 +1,4 @@
 def div(a, b):
+    if b == 0:
+        return 0.0
     return a / b
"""
        # Dry run check
        preview = dry_run_patch(repo_dir, diff)
        assert "src/calc.py" in preview

        # Apply patch
        modified = apply_patch(repo_dir, diff)
        assert "src/calc.py" in modified

        updated_content = file_path.read_text(encoding="utf-8")
        assert "if b == 0:" in updated_content
        assert "return 0.0" in updated_content
