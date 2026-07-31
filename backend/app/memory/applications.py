"""
Application tracking store — persistent log of every job application.
Prevents duplicate applications and provides history for reporting.
"""
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from app.config import APPLICATIONS_PATH

STATUS_PENDING = "pending"
STATUS_APPLIED = "applied"
STATUS_QUEUED = "queued"       # materials ready, owner opens manually
STATUS_SKIPPED = "skipped"
STATUS_SUSPICIOUS = "suspicious"  # flagged by legitimacy check


def _load() -> dict:
    if not APPLICATIONS_PATH.exists():
        return {"applications": {}}
    try:
        return json.loads(APPLICATIONS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"applications": {}}


def _save(data: dict) -> None:
    APPLICATIONS_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def exists(job_id: str) -> bool:
    return job_id in _load()["applications"]


def add(job: dict, status: str = STATUS_PENDING, resume_path: str = "", cover_letter: str = "") -> dict:
    data = _load()
    record = {
        "job_id":        job.get("job_id", ""),
        "title":         job.get("title", ""),
        "company":       job.get("company", ""),
        "url":           job.get("url", ""),
        "source":        job.get("source", ""),
        "snippet":       job.get("snippet", "")[:300],
        "score":         job.get("score", 0),
        "legitimacy":    job.get("legitimacy", "unverified"),
        "flags":         job.get("legitimacy_flags", []),
        "status":        status,
        "added_at":      datetime.now(timezone.utc).isoformat(),
        "applied_at":    None,
        "resume_path":   resume_path,
        "cover_letter":  cover_letter,
    }
    data["applications"][record["job_id"]] = record
    _save(data)
    return record


def update(job_id: str, **fields) -> None:
    data = _load()
    if job_id not in data["applications"]:
        return
    data["applications"][job_id].update(fields)
    if fields.get("status") == STATUS_APPLIED:
        data["applications"][job_id]["applied_at"] = datetime.now(timezone.utc).isoformat()
    _save(data)


def get_all(status: str | None = None) -> list[dict]:
    data = _load()
    apps = list(data["applications"].values())
    if status:
        apps = [a for a in apps if a["status"] == status]
    return sorted(apps, key=lambda x: x["added_at"], reverse=True)


def get_today() -> list[dict]:
    today = date.today().isoformat()
    return [
        a for a in get_all()
        if (a.get("applied_at") or a.get("added_at") or "").startswith(today)
    ]


def stats() -> dict:
    apps = get_all()
    counts = Counter(a["status"] for a in apps)
    return {
        "total":      len(apps),
        "applied":    counts.get(STATUS_APPLIED, 0),
        "queued":     counts.get(STATUS_QUEUED, 0),
        "pending":    counts.get(STATUS_PENDING, 0),
        "skipped":    counts.get(STATUS_SKIPPED, 0),
        "suspicious": counts.get(STATUS_SUSPICIOUS, 0),
        "today":      len(get_today()),
    }


def format_summary(limit: int = 10) -> str:
    s = stats()
    lines = [
        f"Applications — total: {s['total']} | applied: {s['applied']} | "
        f"queued: {s['queued']} | suspicious: {s['suspicious']} | today: {s['today']}",
        "",
    ]
    recent = [a for a in get_all() if a["status"] in (STATUS_APPLIED, STATUS_QUEUED)][:limit]
    for a in recent:
        flag = " ⚠" if a["flags"] else ""
        lines.append(
            f"  [{a['status'].upper()}] {a['title']} @ {a['company'] or 'Unknown'}"
            f"{flag} — {a['url'][:60]}"
        )
    return "\n".join(lines) if recent else "No applications yet."
