import re
from pathlib import Path

# Derive project paths from this file's location:
# resolver.py → execution/ → app/ → backend/ → project root
_BACKEND_DIR = str(Path(__file__).resolve().parents[2])
_PROJECT_ROOT = str(Path(__file__).resolve().parents[3])
_FRONTEND_DIR = str(Path(__file__).resolve().parents[3] / "frontend")


def resolve_action(user_input: str, domain: str, task_type: str) -> dict:
    """
    Map an approved user request to an executable action spec.

    Returns one of:
      {"type": "shell",                "program": str, "args": list, "cwd": str}
      {"type": "integration_required", "message": str}
      {"type": "unresolved",           "message": str}
    """
    text = user_input.lower().strip()

    # Finance domain — real execution requires Sprint 4 integrations
    if domain == "finance":
        return {
            "type": "integration_required",
            "message": (
                "Finance execution (trades, transfers, payments) requires external "
                "integrations not yet configured. Coming in Phase 2 Sprint 4."
            ),
        }

    # Deployment patterns — require CI/CD integration
    if re.search(r"\b(deploy|release|publish|push\s+to\s+prod)\b", text):
        return {
            "type": "integration_required",
            "message": "Deployment execution requires CI/CD integration not yet configured.",
        }

    # ── Git operations ─────────────────────────────────────────────────────────

    if re.search(r"\bgit\s+status\b", text):
        return {"type": "shell", "program": "git", "args": ["status"], "cwd": _PROJECT_ROOT}

    if re.search(r"\bgit\s+log\b", text):
        return {"type": "shell", "program": "git", "args": ["log", "--oneline", "-15"], "cwd": _PROJECT_ROOT}

    if re.search(r"\bgit\s+diff\b", text):
        return {"type": "shell", "program": "git", "args": ["diff", "--stat"], "cwd": _PROJECT_ROOT}

    if re.search(r"\bgit\s+fetch\b", text):
        return {"type": "shell", "program": "git", "args": ["fetch", "--dry-run"], "cwd": _PROJECT_ROOT}

    if re.search(r"\bgit\s+branch\b", text):
        return {"type": "shell", "program": "git", "args": ["branch", "-v"], "cwd": _PROJECT_ROOT}

    # ── Test execution ──────────────────────────────────────────────────────────

    if re.search(r"\b(run|execute|run\s+the)\s+(tests?|pytest|test\s+suite|unit\s+tests?)\b", text):
        return {
            "type": "shell",
            "program": "python",
            "args": ["-m", "pytest", "--tb=short", "-q"],
            "cwd": _PROJECT_ROOT,
        }

    # ── Frontend build ──────────────────────────────────────────────────────────

    if re.search(r"\b(build|compile)\s+(frontend|react|vite|ui|the\s+frontend)\b", text):
        return {
            "type": "shell",
            "program": "npm",
            "args": ["run", "build"],
            "cwd": _FRONTEND_DIR,
        }

    if re.search(r"\bnpm\s+install\b", text):
        return {
            "type": "shell",
            "program": "npm",
            "args": ["install"],
            "cwd": _FRONTEND_DIR,
        }

    # ── Python dependency install ───────────────────────────────────────────────

    if re.search(r"\b(install|update)\s+(python\s+)?(dependencies|packages|deps|requirements)\b", text):
        return {
            "type": "shell",
            "program": "pip",
            "args": ["install", "-r", "requirements.txt"],
            "cwd": _BACKEND_DIR,
        }

    # ── Directory listing ───────────────────────────────────────────────────────

    if re.search(r"\b(list|show)\s+(files|directory|dir|folder)\b", text):
        return {"type": "shell", "program": "ls", "args": ["-la"], "cwd": _PROJECT_ROOT}

    # ── Default: unresolved ─────────────────────────────────────────────────────

    return {
        "type": "unresolved",
        "message": (
            f"Could not map this request to a specific executable action: "
            f"'{user_input[:100]}'. Manual execution required."
        ),
    }
