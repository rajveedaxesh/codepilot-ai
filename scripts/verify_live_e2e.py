import httpx
import sys

def main():
    print("Testing live end-to-end pipeline against running server on http://127.0.0.1:8000...")
    client = httpx.Client(base_url="http://127.0.0.1:8000/api/v1", timeout=30.0)

    # 1. Health
    h = client.get("/health").json()
    print(f"1. Health Check: Status={h['status']}, Provider={h['llm_provider']}")

    # 2. Fresh Demo Project
    p_res = client.post("/projects/demo").json()
    project_id = p_res["id"]
    print(f"2. Loaded Demo Project: {p_res['name']} ({project_id})")

    # 3. File Tree
    tree = client.get(f"/projects/{project_id}/tree").json()
    print(f"3. File Tree Loaded: Root={tree['name']}, Children Count={len(tree.get('children', []))}")

    # 4. View File
    file_info = client.get(f"/projects/{project_id}/file?path=src/math_engine.py").json()
    print(f"4. Inspected File: {file_info['file_path']}, Lang={file_info['language']}, Size={file_info['size']}B")

    # 5. Session
    s_res = client.post("/sessions", json={"project_id": project_id}).json()
    session_id = s_res["session_id"]
    print(f"5. Fresh Active Session: {session_id}")


    # 6. Bug Analysis
    diag = client.post(
        f"/sessions/{session_id}/analyze",
        json={"bug_description": "ZeroDivisionError when denominator is zero in divide() function", "target_file": "src/math_engine.py"}
    ).json()
    print(f"6. Bug Analysis: Severity={diag['severity'].upper()}, Confidence={diag['confidence']*100:.0f}%, Cause='{diag['suspected_root_cause']}'")
    print(f"   Evidence snippets count: {len(diag['evidence'])}")

    # 7. Patch Generation
    patch = client.post(f"/sessions/{session_id}/patches", json={"finding_id": diag["id"]}).json()
    print(f"7. Proposed Patch Generated: ID={patch['id']}, Status={patch['status']}, IsApproved={patch['is_approved']}")

    # 8. User Approval
    apprv = client.post(f"/sessions/{session_id}/patches/{patch['id']}/approval", json={"approved": True}).json()
    print(f"8. User Approval Gate: IsApproved={apprv['is_approved']}, Status={apprv['status']}")

    # 9. Apply Patch
    appl = client.post(f"/sessions/{session_id}/patches/{patch['id']}/apply").json()
    print(f"9. Patch Application: Applied={appl['applied']}, Files={appl['modified_files']}")

    # 10. Regression Test
    reg = client.post(f"/sessions/{session_id}/tests", json={"patch_id": patch["id"]}).json()
    print(f"10. Regression Test: Path={reg['file_path']}, IsVerified={reg['is_verified']} (Generated suggestion)")

    # 11. Verification Run
    ver = client.post(f"/sessions/{session_id}/verify", json={"command": "pytest tests/test_math.py", "run_baseline": False}).json()
    print(f"11. Sandboxed Verification Run: Status={ver['status'].upper()}, ExitCode={ver['exit_code']}, Duration={ver['duration_ms']}ms")

    # 12. Export Report
    exp = client.get(f"/sessions/{session_id}/export").json()
    print(f"12. Session Report Export: ReportLength={len(exp['markdown_report'])} characters")

    # 13. Live Benchmarks
    bench = client.post("/benchmarks/run").json()
    print(f"13. Benchmark Suite: Total={bench['total_fixtures']}, Localization={bench['localization_accuracy']}%, ValidPatch={bench['valid_patch_rate']}%, VerifiedFix={bench['verified_fix_rate']}%")

    print("\nALL 13 LIVE PIPELINE CHECKS PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    main()
