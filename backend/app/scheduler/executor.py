"""
Runs a scheduled task prompt through the BLACK orchestrator chain
and fires a macOS notification with the result summary.
"""
import subprocess

from app.orchestrator.chain import resolve_system, run_chain
from app.orchestrator.context import build_prompt
from app.scheduler.store import record_run


def _notify(title: str, message: str) -> None:
    safe = message.replace('"', "'")[:200]
    subprocess.run(
        ["osascript", "-e",
         f'display notification "{safe}" with title "Mr.Black — {title}" sound name "Ping"'],
        check=False,
    )


_IGBO_SENTINELS = {
    "__igbo_sweep__": ("igbo_sweep", lambda: __import__(
        "app.services.igbo_learning", fromlist=["research_sweep"]).research_sweep()),
    "__igbo_sync__": ("igbo_sync", lambda: __import__(
        "app.services.igbo_learning", fromlist=["sync_from_seed"]).sync_from_seed()),
    "__igbo_gloss__": ("igbo_gloss", lambda: __import__(
        "app.services.igbo_learning", fromlist=["gloss_unverified"]).gloss_unverified()),
}


def run_scheduled_task(task: dict) -> None:
    """Execute a scheduled task and notify with its summary."""
    task_id = task["id"]
    name = task["name"]
    prompt_text = task["prompt"]
    domain = task.get("domain", "general")

    # Direct function dispatch for Igbo learning tasks
    if prompt_text in _IGBO_SENTINELS:
        label, fn = _IGBO_SENTINELS[prompt_text]
        try:
            result = fn()
            summary = str(result)[:300]
            record_run(task_id, summary)
            status = result.get("status", "")
            added = result.get("added", result.get("items", ""))
            _notify(name, f"{status} — {added} words" if added else status)
        except Exception as exc:
            error = str(exc)[:200]
            record_run(task_id, f"ERROR: {error}")
            _notify(f"{name} — Error", error)
        return

    try:
        prompt, _ = build_prompt(prompt_text)
        system, agent = resolve_system("researcher", domain, prompt_text)
        result = run_chain(
            agent_name=agent,
            task_type="research",
            domain=domain,
            prompt=prompt,
            session_id=f"sched-{task_id}",
            user_input=prompt_text,
        )
        summary = result.get("reply", "")[:300]
        record_run(task_id, summary)
        _notify(name, summary)
    except Exception as exc:
        error = str(exc)[:200]
        record_run(task_id, f"ERROR: {error}")
        _notify(f"{name} — Error", error)
