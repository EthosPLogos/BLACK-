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


def run_scheduled_task(task: dict) -> None:
    """Execute a scheduled task and notify with its summary."""
    task_id = task["id"]
    name = task["name"]
    prompt_text = task["prompt"]
    domain = task.get("domain", "general")

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
