import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import APIRouter

from app.config import OLLAMA_URL
from urllib.parse import urlparse

router = APIRouter(prefix="/api/system", tags=["Update Intel"])

ROOT = Path(__file__).resolve().parents[3]  # black/backend/
VENV_PIP = ROOT / ".venv" / "bin" / "pip"
FRONTEND = ROOT.parent / "frontend"


def _pip_outdated() -> list[dict]:
    pip_bin = str(VENV_PIP) if VENV_PIP.exists() else sys.executable.replace("python", "pip").replace("python3", "pip3")
    try:
        result = subprocess.run(
            [pip_bin, "list", "--outdated", "--format=json"],
            capture_output=True, text=True, timeout=30
        )
        return json.loads(result.stdout) if result.stdout.strip() else []
    except Exception:
        try:
            result = subprocess.run(
                ["pip3", "list", "--outdated", "--format=json"],
                capture_output=True, text=True, timeout=30
            )
            return json.loads(result.stdout) if result.stdout.strip() else []
        except Exception:
            return []


def _npm_outdated() -> dict:
    if not FRONTEND.exists():
        return {}
    try:
        result = subprocess.run(
            ["npm", "outdated", "--json"],
            capture_output=True, text=True, timeout=30, cwd=str(FRONTEND)
        )
        # npm outdated exits 1 when outdated packages exist — that's normal
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except Exception:
        return {}


def _ollama_models() -> list[dict]:
    base = f"{urlparse(OLLAMA_URL).scheme}://{urlparse(OLLAMA_URL).netloc}"
    try:
        r = httpx.get(f"{base}/api/tags", timeout=5.0)
        if r.status_code == 200:
            models = r.json().get("models", [])
            return [
                {
                    "name": m.get("name"),
                    "size_gb": round(m.get("size", 0) / 1e9, 1),
                    "modified": m.get("modified_at", "")[:10],
                }
                for m in models
            ]
    except Exception:
        pass
    return []


def _security_priority(packages: list[dict]) -> list[dict]:
    """Flag packages that are security-critical so they're surfaced first."""
    critical = {
        "fastapi", "uvicorn", "starlette", "httpx", "cryptography",
        "pyjwt", "python-multipart", "requests", "urllib3", "certifi",
    }
    for p in packages:
        p["security_critical"] = p.get("name", "").lower() in critical
    return sorted(packages, key=lambda p: (not p["security_critical"], p.get("name", "")))


@router.get("/update-check")
def update_check():
    """Run a full system update sweep — packages, models, versions."""
    backend_outdated = _security_priority(_pip_outdated())
    frontend_outdated = _npm_outdated()
    ollama_models = _ollama_models()

    summary = {
        "backend_outdated_count": len(backend_outdated),
        "frontend_outdated_count": len(frontend_outdated),
        "ollama_models_installed": len(ollama_models),
        "security_critical_updates": sum(1 for p in backend_outdated if p.get("security_critical")),
    }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "backend_outdated": backend_outdated,
        "frontend_outdated": frontend_outdated,
        "ollama_models": ollama_models,
    }
