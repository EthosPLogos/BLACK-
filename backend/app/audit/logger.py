from datetime import datetime, timezone

from app.audit.store import append


def log_event(event_type: str, details: dict, session_id: str = "") -> None:
    append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "event_type": event_type,
            "details": details,
        }
    )
