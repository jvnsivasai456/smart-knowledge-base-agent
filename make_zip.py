import os
import zipfile

def build_zip():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(project_dir, "smart-knowledge-base-agent.zip")

    exclude_dirs = {".git", "venv", "__pycache__", ".pytest_cache", ".devcontainer"}
    exclude_files = {"smart-knowledge-base-agent.zip", "cloudflared.exe"}

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in files:
                if f in exclude_files or f.endswith(".pyc"):
                    continue
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, project_dir)
                zf.write(full_path, os.path.join("smart-knowledge-base-agent", rel_path))

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"[OK] Generated {zip_path} ({size_mb:.2f} MB)")
    return zip_path

if __name__ == "__main__":
    build_zip()
