"""
Safe file writer for Black Forge project scaffolding.
All writes are restricted to PROJECTS_BASE_DIR — path traversal is rejected at the path level.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

PROJECTS_BASE_DIR = Path.home() / "Mr.Black" / "projects"


def _safe_resolve(project_name: str, relative_path: str) -> Path:
    base = (PROJECTS_BASE_DIR / project_name).resolve()
    target = (base / relative_path.lstrip("/")).resolve()
    if not target.is_relative_to(base):
        raise ValueError(f"Path traversal rejected: {relative_path!r}")
    return target


def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")[:48] or "project"


def write_project_files(project_name: str, files: list[dict]) -> dict:
    """
    Write [{path, content}] into ~/Mr.Black/projects/{project_name}/.
    Creates parent directories as needed. Returns a write summary.
    """
    project_dir = PROJECTS_BASE_DIR / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    errors: list[dict] = []

    for f in files:
        rel = (f.get("path") or "").lstrip("/")
        content = f.get("content") or ""
        if not rel:
            continue
        try:
            target = _safe_resolve(project_name, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(rel)
        except Exception as exc:
            errors.append({"path": rel, "error": str(exc)[:200]})

    manifest = {
        "project_name": project_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_dir": str(project_dir),
        "files": written,
    }
    (project_dir / ".forge_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    return {
        "project_dir": str(project_dir),
        "written": written,
        "errors": errors,
        "file_count": len(written),
    }


def list_projects() -> list[dict]:
    if not PROJECTS_BASE_DIR.exists():
        return []
    projects = []
    for d in sorted(PROJECTS_BASE_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        manifest_path = d / ".forge_manifest.json"
        if manifest_path.exists():
            try:
                projects.append(json.loads(manifest_path.read_text()))
            except Exception:
                projects.append({"project_name": d.name})
        else:
            projects.append({"project_name": d.name})
    return projects


def get_project_tree(project_name: str) -> dict:
    project_dir = PROJECTS_BASE_DIR / project_name
    if not project_dir.exists():
        return {"error": f"Project '{project_name}' not found"}
    files = [
        str(f.relative_to(project_dir))
        for f in sorted(project_dir.rglob("*"))
        if f.is_file() and not f.name.startswith(".")
    ]
    return {"project_name": project_name, "path": str(project_dir), "files": files}


def read_project_file(project_name: str, relative_path: str) -> str:
    target = _safe_resolve(project_name, relative_path)
    if not target.exists():
        raise FileNotFoundError(f"{relative_path} not found in project {project_name!r}")
    return target.read_text(encoding="utf-8")
