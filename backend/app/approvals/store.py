import json
import subprocess
from datetime import datetime, timezone

from app.config import APPROVALS_PATH
from app.approvals.models import APPROVED, EXECUTED, PENDING, REJECTED


def _notify_approval(record: dict) -> None:
    msg = record.get("user_input", "Action requires review")[:80]
    subprocess.run(
        ["osascript", "-e",
         f'display notification "{msg}" with title "Mr.Black — Approval Required" '
         f'subtitle "Open the approval panel to review" sound name "Sosumi"'],
        check=False,
    )


def _load() -> dict:
    if not APPROVALS_PATH.exists():
        return {"records": {}}
    try:
        return json.loads(APPROVALS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"records": {}}


def _save(data: dict) -> None:
    APPROVALS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def add_approval(record: dict) -> None:
    data = _load()
    data["records"][record["id"]] = record
    _save(data)
    _notify_approval(record)


def get_pending() -> list[dict]:
    data = _load()
    return sorted(
        [r for r in data["records"].values() if r["status"] == PENDING],
        key=lambda r: r["timestamp"],
    )


def get_all() -> list[dict]:
    data = _load()
    return sorted(data["records"].values(), key=lambda r: r["timestamp"], reverse=True)


def get_by_id(approval_id: str) -> dict | None:
    return _load()["records"].get(approval_id)


def resolve(approval_id: str, status: str) -> dict | None:
    data = _load()
    record = data["records"].get(approval_id)
    if not record:
        return None
    if record["status"] != PENDING:
        return record  # already resolved — return as-is
    record["status"] = status
    record["resolved_at"] = datetime.now(timezone.utc).isoformat()
    _save(data)
    return record


def mark_executed(approval_id: str, execution_result: dict) -> dict | None:
    data = _load()
    record = data["records"].get(approval_id)
    if not record:
        return None
    if record["status"] == EXECUTED:
        return record  # idempotent
    now = datetime.now(timezone.utc).isoformat()
    record["status"] = EXECUTED
    record["resolved_at"] = record.get("resolved_at") or now
    record["executed_at"] = now
    record["execution_result"] = execution_result
    _save(data)
    return record
