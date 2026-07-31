from fastapi import APIRouter, HTTPException, Query

from app.integrations import email_integration

router = APIRouter(prefix="/api/email", tags=["email"])


@router.get("/status")
def email_status():
    configured = email_integration.is_configured()
    if not configured:
        return {"configured": False, "message": "Set EMAIL_HOST, EMAIL_USER, and EMAIL_PASSWORD in .env"}
    try:
        count = email_integration.get_unread_count()
        return {"configured": True, "unread": count}
    except Exception as e:
        return {"configured": True, "error": str(e), "unread": 0}


@router.get("/inbox")
def get_inbox(
    limit: int = Query(default=10, ge=1, le=50),
    unread_only: bool = Query(default=False),
):
    if not email_integration.is_configured():
        raise HTTPException(status_code=503, detail="Email not configured")
    emails = email_integration.get_emails(limit=limit, unread_only=unread_only)
    return {"emails": emails, "count": len(emails)}


@router.get("/search")
def search_email(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
):
    if not email_integration.is_configured():
        raise HTTPException(status_code=503, detail="Email not configured")
    results = email_integration.search_emails(query=q, limit=limit)
    return {"emails": results, "count": len(results)}
