from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.scheduler import runner, store

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


class TaskCreate(BaseModel):
    name: str
    prompt: str
    cron: str
    domain: str = "general"


class TaskToggle(BaseModel):
    enabled: bool


@router.get("")
def list_tasks():
    return {"tasks": store.get_all_tasks()}


@router.post("")
def create_task(body: TaskCreate):
    parts = body.cron.strip().split()
    if len(parts) != 5:
        raise HTTPException(status_code=400, detail="cron must be 5 fields: minute hour day month weekday")
    task = store.create_task(
        name=body.name,
        prompt=body.prompt,
        cron=body.cron.strip(),
        domain=body.domain,
    )
    runner.register_task(task)
    return task


@router.patch("/{task_id}")
def toggle_task(task_id: str, body: TaskToggle):
    task = store.update_task(task_id, enabled=body.enabled)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    runner.set_task_enabled(task)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: str):
    if not store.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    runner.unregister_task(task_id)
    return {"deleted": task_id}


@router.post("/{task_id}/run")
def run_now(task_id: str):
    """Manually trigger a task immediately."""
    task = store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    from app.scheduler.executor import run_scheduled_task
    run_scheduled_task(task)
    return {"triggered": task_id}


@router.get("/watchdog")
def watchdog_now():
    """Manually trigger the watchdog health check."""
    from app.scheduler.watchdog import run_watchdog
    return run_watchdog()
