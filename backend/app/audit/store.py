import json
from datetime import datetime, timezone

from app.config import AUDIT_LOG_PATH

_MAX_AUDIT_LINES = 10_000


def _rotate_if_needed() -> None:
    if not AUDIT_LOG_PATH.exists():
        return
    try:
        lines = AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()
        if len(lines) > _MAX_AUDIT_LINES:
            AUDIT_LOG_PATH.write_text(
                "\n".join(lines[-_MAX_AUDIT_LINES:]) + "\n",
                encoding="utf-8",
            )
    except OSError:
        pass


def _pg_append(record: dict) -> None:
    """Dual-write to Postgres when available. Silently skipped if DB not configured."""
    try:
        from app.db.session import get_session, is_available
        if not is_available():
            return
        from app.db.models import AuditEvent
        with get_session() as session:
            session.add(AuditEvent(
                session_id=record.get("session_id"),
                event_type=record.get("event", "unknown"),
                payload={k: v for k, v in record.items()
                         if k not in ("event", "session_id", "ts")},
            ))
    except Exception:
        pass  # Never let DB errors break the audit trail


def append(record: dict) -> None:
    _rotate_if_needed()
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    _pg_append(record)


def read_recent(limit: int = 100) -> list[dict]:
    if not AUDIT_LOG_PATH.exists():
        return []
    lines = AUDIT_LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    records = []
    for line in lines[-limit:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return records


def count() -> int:
    if not AUDIT_LOG_PATH.exists():
        return 0
    try:
        with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return 0
