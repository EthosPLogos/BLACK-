"""
System health watchdog — runs every 5 minutes via the scheduler.
Checks Ollama, memory capacity, pending approvals, and audit log size.
Fires a macOS notification only when something needs attention.
"""
import subprocess

from app.approvals.store import get_pending
from app.audit.store import count as audit_count
from app.config import MAX_CONVERSATIONS, MAX_FACTS
from app.memory.store import get_memory_stats
from app.services.ollama_client import invalidate_probe_cache, is_ollama_available


def _alert(message: str) -> None:
    safe = message.replace('"', "'")
    subprocess.run(
        ["osascript", "-e",
         f'display notification "{safe}" with title "Mr.Black — Health Warning" sound name "Basso"'],
        check=False,
    )


def run_watchdog() -> dict:
    """Run all health checks. Returns a summary dict for the status endpoint."""
    issues: list[str] = []

    # Ollama
    invalidate_probe_cache()
    ollama_ok = is_ollama_available()
    if not ollama_ok:
        issues.append("Ollama is unreachable — local inference offline")

    # Memory capacity
    stats = get_memory_stats()
    conv_count = stats.get("conversation_count", 0)
    fact_count = stats.get("fact_count", 0)
    if conv_count >= MAX_CONVERSATIONS * 0.9:
        issues.append(f"Memory near capacity: {conv_count}/{MAX_CONVERSATIONS} conversations")
    if fact_count >= MAX_FACTS * 0.9:
        issues.append(f"Facts near capacity: {fact_count}/{MAX_FACTS} facts")

    # Pending approvals
    pending = get_pending()
    if len(pending) >= 5:
        issues.append(f"{len(pending)} actions waiting in the approval queue")

    # Audit log
    audit_total = audit_count()
    if audit_total >= 10_000:
        issues.append(f"Audit log has {audit_total:,} entries — consider archiving")

    for issue in issues:
        _alert(issue)

    return {
        "ollama_ok": ollama_ok,
        "conversation_count": conv_count,
        "fact_count": fact_count,
        "pending_approvals": len(pending),
        "audit_count": audit_total,
        "issues": issues,
    }
