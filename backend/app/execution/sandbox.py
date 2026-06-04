import subprocess

# Explicit allowlist — nothing outside this set will be run.
ALLOWED_PROGRAMS = {
    "git",
    "python", "python3",
    "pip", "pip3",
    "npm", "npx", "node",
    "pytest",
    "uvicorn",
    "ls", "find", "cat", "head", "tail",
}

DEFAULT_TIMEOUT = 30
MAX_OUTPUT_BYTES = 10_000


def run_command(
    program: str,
    args: list[str],
    cwd: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """
    Execute a sandboxed subprocess. Only programs in ALLOWED_PROGRAMS can run.
    Returns {"success": bool, "output": str, "returncode": int, "error": str | None}
    """
    if program not in ALLOWED_PROGRAMS:
        return {
            "success": False,
            "output": "",
            "returncode": -1,
            "error": f"'{program}' is not in the execution allowlist.",
        }

    try:
        result = subprocess.run(
            [program] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        raw = result.stdout + result.stderr
        if len(raw.encode()) > MAX_OUTPUT_BYTES:
            raw = raw[:MAX_OUTPUT_BYTES] + "\n[output truncated]"
        return {
            "success": result.returncode == 0,
            "output": raw.strip(),
            "returncode": result.returncode,
            "error": None,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "returncode": -1, "error": f"Timed out after {timeout}s"}
    except FileNotFoundError:
        return {"success": False, "output": "", "returncode": -1, "error": f"Program '{program}' not found on system"}
    except Exception as exc:
        return {"success": False, "output": "", "returncode": -1, "error": str(exc)}
