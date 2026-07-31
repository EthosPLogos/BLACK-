"""
APScheduler-backed task runner.
Started on FastAPI startup, stopped on shutdown.
Loads all enabled tasks from the store and schedules them by cron expression.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.scheduler.executor import run_scheduled_task
from app.scheduler.store import get_all_tasks
from app.scheduler.watchdog import run_watchdog

_scheduler = BackgroundScheduler(timezone="UTC")
_WATCHDOG_JOB_ID = "__watchdog__"
_JOB_APPLY_ID = "__job_apply__"
_WATCHDOG_INTERVAL_MINUTES = 5


def _task_job(task_id: str) -> None:
    from app.scheduler.store import get_task
    task = get_task(task_id)
    if task and task.get("enabled"):
        run_scheduled_task(task)


def start() -> None:
    """Load all persisted tasks and start the scheduler + watchdog."""
    for task in get_all_tasks():
        if task.get("enabled"):
            _add_job(task)

    # Built-in watchdog — always runs regardless of user tasks
    _scheduler.add_job(
        run_watchdog,
        trigger="interval",
        minutes=_WATCHDOG_INTERVAL_MINUTES,
        id=_WATCHDOG_JOB_ID,
        replace_existing=True,
    )

    # Job Apply — register if enabled
    _sync_job_apply()

    _scheduler.start()


def _sync_job_apply() -> None:
    """Register or remove the job apply cron based on current config."""
    try:
        from app.services.job_apply_engine import load_criteria, run_apply_cycle
        criteria = load_criteria()
        if criteria.get("enabled"):
            cron_parts = criteria.get("run_cron", "0 9 * * 1-5").split()
            if len(cron_parts) == 5:
                minute, hour, day, month, dow = cron_parts
                _scheduler.add_job(
                    run_apply_cycle,
                    trigger=CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=dow),
                    id=_JOB_APPLY_ID,
                    replace_existing=True,
                )
        else:
            if _scheduler.get_job(_JOB_APPLY_ID):
                _scheduler.remove_job(_JOB_APPLY_ID)
    except Exception:
        pass


def refresh_job_apply() -> None:
    """Called when job apply is enabled/disabled via the API."""
    _sync_job_apply()


def stop() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)


def _add_job(task: dict) -> None:
    parts = task["cron"].split()
    if len(parts) != 5:
        return
    minute, hour, day, month, day_of_week = parts
    _scheduler.add_job(
        _task_job,
        trigger=CronTrigger(
            minute=minute, hour=hour, day=day,
            month=month, day_of_week=day_of_week,
        ),
        id=task["id"],
        args=[task["id"]],
        replace_existing=True,
    )


def register_task(task: dict) -> None:
    """Called after a new task is created via the API."""
    if task.get("enabled"):
        _add_job(task)


def unregister_task(task_id: str) -> None:
    """Called after a task is deleted via the API."""
    if _scheduler.get_job(task_id):
        _scheduler.remove_job(task_id)


def set_task_enabled(task: dict) -> None:
    """Called when a task is toggled on/off via the API."""
    if task.get("enabled"):
        _add_job(task)
    else:
        if _scheduler.get_job(task["id"]):
            _scheduler.remove_job(task["id"])
