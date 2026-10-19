import io
from fastapi.testclient import TestClient

def test_full_api_workflow(client: TestClient, sample_zip_bytes: bytes):
    # 1. Upload repository ZIP
    files = {"file": ("sample.zip", sample_zip_bytes, "application/zip")}
    response = client.post("/api/v1/projects/upload", files=files, data={"project_name": "MathService"})
    assert response.status_code == 200, response.text
    project_data = response.json()
    project_id = project_data["id"]
    assert project_data["name"] == "MathService"
    assert "python" in project_data["languages"]

    # 2. Inspect repository file tree
    tree_resp = client.get(f"/api/v1/projects/{project_id}/tree")
    assert tree_resp.status_code == 200
    tree_data = tree_resp.json()
    assert tree_data["type"] == "directory"

    # 3. Read specific source file
    file_resp = client.get(f"/api/v1/projects/{project_id}/file?path=src/math_engine.py")
    assert file_resp.status_code == 200
    file_data = file_resp.json()
    assert "divide" in file_data["content"]
    assert file_data["language"] == "python"

    # 4. Create analysis session
    session_create_resp = client.post("/api/v1/sessions", json={
        "project_id": project_id,
        "bug_description": "ZeroDivisionError when denominator is zero in divide() function",
        "target_file": "src/math_engine.py"
    })
    assert session_create_resp.status_code == 200
    session_id = session_create_resp.json()["session_id"]

    # 5. Start bug analysis
    analysis_resp = client.post(f"/api/v1/sessions/{session_id}/analyze", json={
        "bug_description": "ZeroDivisionError when denominator is zero in divide() function",
        "target_file": "src/math_engine.py"
    })
    assert analysis_resp.status_code == 200
    finding = analysis_resp.json()
    assert finding["severity"] in ["low", "medium", "high", "critical"]
    assert "division" in finding["suspected_root_cause"].lower() or "missing guard" in finding["suspected_root_cause"].lower()
    assert len(finding["evidence"]) > 0

    # 6. Generate proposed patch
    patch_resp = client.post(f"/api/v1/sessions/{session_id}/patches", json={
        "finding_id": finding["id"]
    })
    assert patch_resp.status_code == 200
    patch = patch_resp.json()
    patch_id = patch["id"]
    assert "--- a/src/math_engine.py" in patch["diff_content"]
    assert patch["is_approved"] is False  # Explicit approval REQUIRED!

    # 6b. Verify that unapproved patch CANNOT be applied (Approval Gate)
    unapproved_apply = client.post(f"/api/v1/sessions/{session_id}/patches/{patch_id}/apply")
    assert unapproved_apply.status_code == 400
    assert "explicit user approval" in unapproved_apply.json()["detail"].lower()

    # 7. Approve patch explicitly
    approval_resp = client.post(f"/api/v1/sessions/{session_id}/patches/{patch_id}/approval", json={
        "approved": True
    })

    assert approval_resp.status_code == 200
    assert approval_resp.json()["is_approved"] is True

    # 8. Generate regression test
    test_resp = client.post(f"/api/v1/sessions/{session_id}/tests", json={
        "patch_id": patch_id
    })
    assert test_resp.status_code == 200
    test_data = test_resp.json()
    assert "def test_" in test_data["test_code"]
    assert test_data["is_verified"] is False  # Never claim code is verified before running tests!

    # 9. Execute isolated verification run
    verify_resp = client.post(f"/api/v1/sessions/{session_id}/verify", json={
        "command": "pytest tests/test_math.py",
        "run_baseline": False
    })
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert "exit_code" in verify_data
    assert "duration_ms" in verify_data
    assert "stdout" in verify_data

    # 10. Export session report in Markdown and JSON
    export_resp = client.get(f"/api/v1/sessions/{session_id}/export")
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert "# CodePilot AI" in export_data["markdown_report"]
    assert export_data["session_id"] == session_id
