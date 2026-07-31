"""
Job Apply management API.
Start/stop daily runs, upload resume, set criteria, view history.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.memory.applications import (
    format_summary, get_all, stats,
    STATUS_APPLIED, STATUS_QUEUED, STATUS_SUSPICIOUS,
)
from app.scheduler.runner import refresh_job_apply
from app.services.job_apply_engine import (
    get_base_resume, load_criteria, run_apply_cycle,
    save_base_resume, save_base_resume_bytes, save_criteria, set_enabled,
)

router = APIRouter(prefix="/api/jobs", tags=["Job Apply"])


class CriteriaUpdate(BaseModel):
    titles: list[str] | None = None
    location: str | None = None
    min_score: int | None = None
    daily_limit: int | None = None
    exclude_companies: list[str] | None = None
    require_keywords: list[str] | None = None
    run_cron: str | None = None


@router.get("/status")
def job_status():
    criteria = load_criteria()
    s = stats()
    return {
        "enabled": criteria.get("enabled", False),
        "criteria": {
            "titles": criteria.get("titles", []),
            "location": criteria.get("location", "remote"),
            "min_score": criteria.get("min_score", 60),
            "daily_limit": criteria.get("daily_limit", 10),
            "run_cron": criteria.get("run_cron", "0 9 * * 1-5"),
        },
        "resume_loaded": bool(get_base_resume()),
        "stats": s,
    }


@router.post("/start")
def start_applying(background_tasks: BackgroundTasks):
    criteria = load_criteria()
    if not get_base_resume():
        raise HTTPException(status_code=400, detail="Upload a resume first via POST /api/jobs/resume")
    if not any(t.strip() for t in criteria.get("titles", [])):
        raise HTTPException(status_code=400, detail="Set job titles first via PATCH /api/jobs/criteria")
    set_enabled(True)
    refresh_job_apply()
    return {"status": "enabled", "message": "Daily job applications started. Running first cycle now."}


@router.post("/stop")
def stop_applying():
    set_enabled(False)
    refresh_job_apply()
    s = stats()
    return {
        "status": "disabled",
        "message": "Daily applications stopped.",
        "total_applied": s["applied"],
        "total_queued": s["queued"],
    }


@router.post("/run-now")
def run_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_apply_cycle)
    return {"status": "running", "message": "Job apply cycle started — check /api/jobs/history for results."}


@router.get("/history")
def history(status: str | None = None, limit: int = 50):
    apps = get_all(status=status)[:limit]
    return {
        "count": len(apps),
        "stats": stats(),
        "applications": apps,
    }


@router.get("/suspicious")
def suspicious_jobs():
    suspicious = get_all(status=STATUS_SUSPICIOUS)
    return {
        "count": len(suspicious),
        "jobs": suspicious,
    }


@router.get("/queued")
def queued_jobs():
    queued = get_all(status=STATUS_QUEUED)
    return {
        "count": len(queued),
        "jobs": queued,
        "message": "These applications have prepared resume + cover letter. Open the URL to complete submission.",
    }


@router.post("/resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload base resume (TXT or DOCX). This becomes the template for all applications."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    data = await file.read()
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()

    if ext == "txt":
        save_base_resume(data.decode("utf-8", errors="replace"))
    elif ext == "docx":
        # Extract text from DOCX
        try:
            import io
            from docx import Document
            doc = Document(io.BytesIO(data))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            save_base_resume(text)
            save_base_resume_bytes(data, file.filename)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not parse DOCX: {exc}")
    elif ext == "pdf":
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            save_base_resume(text)
            save_base_resume_bytes(data, file.filename)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not parse PDF: {exc}")
    else:
        raise HTTPException(status_code=400, detail="Supported formats: TXT, DOCX, PDF")

    preview = get_base_resume()[:200]
    return {
        "status": "saved",
        "filename": file.filename,
        "size_bytes": len(data),
        "preview": preview,
    }


@router.get("/resume")
def get_resume():
    text = get_base_resume()
    if not text:
        return {"loaded": False, "resume": ""}
    return {"loaded": True, "preview": text[:500], "length": len(text)}


@router.patch("/criteria")
def update_criteria(update: CriteriaUpdate):
    current = load_criteria()
    if update.titles is not None:
        current["titles"] = [t.strip() for t in update.titles if t.strip()]
    if update.location is not None:
        current["location"] = update.location
    if update.min_score is not None:
        current["min_score"] = max(0, min(100, update.min_score))
    if update.daily_limit is not None:
        current["daily_limit"] = max(1, min(50, update.daily_limit))
    if update.exclude_companies is not None:
        current["exclude_companies"] = update.exclude_companies
    if update.require_keywords is not None:
        current["require_keywords"] = update.require_keywords
    if update.run_cron is not None:
        current["run_cron"] = update.run_cron
    save_criteria(current)
    return {"status": "updated", "criteria": current}


@router.get("/summary")
def summary():
    return {"summary": format_summary(limit=20)}
