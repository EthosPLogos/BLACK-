from pathlib import Path
from typing import Optional

from app.config import FILE_SEARCH_PATHS

_SKIP_DIRS = frozenset([
    "node_modules", ".git", "__pycache__", ".venv", "venv", ".tox",
    "dist", "build", ".cache", ".next", "coverage",
])

_STOP_WORDS = frozenset([
    "find", "search", "show", "me", "the", "a", "an", "that", "my", "i",
    "file", "folder", "where", "is", "can", "you", "for", "in", "on", "at",
    "with", "look", "locate", "open", "get", "what", "how", "do", "did",
    "have", "had", "has", "was", "were", "are", "be", "been", "its",
])


def search_files(query: str, extensions: Optional[list[str]] = None, limit: int = 20) -> list[dict]:
    query_lower = query.lower()
    results = []
    seen: set[str] = set()

    for base_dir in FILE_SEARCH_PATHS:
        base = Path(base_dir).expanduser().resolve()
        if not base.exists():
            continue
        try:
            for item in base.rglob("*"):
                if not item.is_file():
                    continue
                if any(part.startswith(".") or part in _SKIP_DIRS for part in item.parts):
                    continue
                if extensions and item.suffix.lower() not in extensions:
                    continue
                if query_lower in item.name.lower() and str(item) not in seen:
                    try:
                        stat = item.stat()
                        seen.add(str(item))
                        results.append({
                            "name": item.name,
                            "path": str(item),
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                        })
                    except OSError:
                        continue
                if len(results) >= limit:
                    break
        except PermissionError:
            continue
        if len(results) >= limit:
            break

    results.sort(key=lambda f: f["modified"], reverse=True)
    return results[:limit]


def search_files_for_query(user_input: str, limit: int = 15) -> list[dict]:
    """Extract meaningful tokens from user input and search across all of them."""
    tokens = [
        w.strip(".,?!\"'")
        for w in user_input.lower().split()
        if len(w) > 2 and w.strip(".,?!\"'") not in _STOP_WORDS
    ]
    if not tokens:
        return []

    seen: set[str] = set()
    results: list[dict] = []
    for token in tokens[:4]:
        for r in search_files(token, limit=limit):
            if r["path"] not in seen:
                seen.add(r["path"])
                results.append(r)

    results.sort(key=lambda f: f["modified"], reverse=True)
    return results[:limit]


def read_file_preview(path: str, max_chars: int = 2000) -> str:
    p = Path(path).expanduser().resolve()
    approved = [Path(d).expanduser().resolve() for d in FILE_SEARCH_PATHS]
    if not any(p == a or p.is_relative_to(a) for a in approved):
        return "Access denied: file is outside approved directories."
    try:
        text = p.read_text(errors="replace")
        return text[:max_chars] + ("…" if len(text) > max_chars else "")
    except Exception as e:
        return f"Could not read file: {e}"


def format_search_results(results: list[dict]) -> str:
    if not results:
        return "No matching files found."
    lines = []
    for r in results:
        size_kb = r["size"] / 1024
        lines.append(f"- {r['name']} ({size_kb:.1f} KB) — {r['path']}")
    return "\n".join(lines)
