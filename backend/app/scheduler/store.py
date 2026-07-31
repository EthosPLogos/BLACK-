"""
Persistent storage for scheduled tasks.
Each task is a dict stored in black_schedule.json.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import SCHEDULE_PATH


def _load() -> dict:
    if not SCHEDULE_PATH.exists():
        return {"tasks": {}}
    try:
        return json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"tasks": {}}


def _save(data: dict) -> None:
    SCHEDULE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def create_task(name: str, prompt: str, cron: str, domain: str = "general") -> dict:
    task = {
        "id": uuid.uuid4().hex[:10],
        "name": name,
        "prompt": prompt,
        "cron": cron,
        "domain": domain,
        "enabled": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_run": None,
        "last_result": None,
    }
    data = _load()
    data["tasks"][task["id"]] = task
    _save(data)
    return task


def get_all_tasks() -> list[dict]:
    return list(_load()["tasks"].values())


def get_task(task_id: str) -> dict | None:
    return _load()["tasks"].get(task_id)


def update_task(task_id: str, **fields) -> dict | None:
    data = _load()
    task = data["tasks"].get(task_id)
    if not task:
        return None
    task.update(fields)
    _save(data)
    return task


def delete_task(task_id: str) -> bool:
    data = _load()
    if task_id not in data["tasks"]:
        return False
    del data["tasks"][task_id]
    _save(data)
    return True


def record_run(task_id: str, result_summary: str) -> None:
    data = _load()
    task = data["tasks"].get(task_id)
    if task:
        task["last_run"] = datetime.now(timezone.utc).isoformat()
        task["last_result"] = result_summary[:300]
        _save(data)
