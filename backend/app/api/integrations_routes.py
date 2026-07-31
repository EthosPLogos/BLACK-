from fastapi import APIRouter, HTTPException, Query

from app.integrations import (
    calendar_integration,
    contacts_integration,
    files_integration,
    notes_integration,
    reminders_integration,
    web_search,
)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/calendar/today")
def calendar_today():
    events = calendar_integration.get_today_events()
    return {"events": events, "count": len(events)}


@router.get("/calendar/upcoming")
def calendar_upcoming(days: int = Query(7, ge=1, le=30)):
    events = calendar_integration.get_upcoming_events(days=days)
    return {"events": events, "count": len(events), "days": days}


@router.get("/reminders")
def list_reminders(list_name: str = Query("")):
    reminders = reminders_integration.get_pending_reminders(list_name=list_name)
    return {"reminders": reminders, "count": len(reminders)}


@router.post("/reminders")
def add_reminder(body: dict):
    title = body.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    due_date = body.get("due_date", "")
    list_name = body.get("list_name", "")
    ok = reminders_integration.create_reminder(title=title, due_date=due_date, list_name=list_name)
    return {"success": ok, "title": title}


@router.get("/files/search")
def file_search(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=50)):
    results = files_integration.search_files(query=q, limit=limit)
    return {"results": results, "count": len(results), "query": q}


@router.get("/files/read")
def file_read(path: str = Query(...)):
    content = files_integration.read_file_preview(path=path)
    return {"path": path, "content": content}


@router.get("/notes/search")
def notes_search(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
    results = notes_integration.search_notes(query=q, limit=limit)
    return {"results": results, "count": len(results), "query": q}


@router.get("/contacts/search")
def contacts_search(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=20)):
    results = contacts_integration.search_contacts(query=q, limit=limit)
    return {"results": results, "count": len(results), "query": q}


@router.get("/web/search")
def web_search_endpoint(q: str = Query(..., min_length=1), max_results: int = Query(5, ge=1, le=10)):
    results = web_search.search_web(query=q, max_results=max_results)
    return {"results": results, "count": len(results), "query": q}
