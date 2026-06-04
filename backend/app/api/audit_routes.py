from fastapi import APIRouter, Query

from app.audit.store import read_recent

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("")
def get_audit_log(limit: int = Query(default=100, ge=1, le=1000)):
    records = read_recent(limit)
    return {"count": len(records), "records": records}
