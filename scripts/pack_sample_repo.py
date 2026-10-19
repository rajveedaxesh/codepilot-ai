import os
import zipfile
from pathlib import Path

def create_sample_zip():
    base_dir = Path(__file__).resolve().parent.parent
    sample_dir = base_dir / "sample_repo"
    output_zip = base_dir / "sample_repo.zip"

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(sample_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for f in files:
                if f.endswith(".pyc") or f.startswith("."):
                    continue
                file_path = Path(root) / f
                arc_name = file_path.relative_to(sample_dir)
                zf.write(file_path, arc_name)

    print(f"Sample repository packed successfully into: {output_zip} ({output_zip.stat().st_size} bytes)")
    return output_zip

if __name__ == "__main__":
    create_sample_zip()
