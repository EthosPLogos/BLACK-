from fastapi import APIRouter, HTTPException

from app.agents.execution_agent import run_execution
from app.approvals.models import APPROVED, EXECUTED, PENDING
from app.approvals.store import get_all, get_by_id, get_pending, mark_executed, resolve
from app.audit import logger as audit

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])


@router.get("")
def list_approvals(pending_only: bool = True):
    records = get_pending() if pending_only else get_all()
    return {"count": len(records), "records": records}


@router.get("/{approval_id}")
def get_approval(approval_id: str):
    record = get_by_id(approval_id)
    if not record:
        raise HTTPException(status_code=404, detail="Approval not found")
    return record


@router.post("/{approval_id}/approve")
def approve_action(approval_id: str):
    record = resolve(approval_id, "approved")
    if not record:
        raise HTTPException(status_code=404, detail="Approval not found")
    audit.log_event(
        "owner_approved",
        {
            "approval_id": approval_id,
            "domain": record.get("domain"),
            "task_type": record.get("task_type"),
            "input_preview": record.get("user_input", "")[:120],
        },
    )
    return {"status": "approved", "record": record}


@router.post("/{approval_id}/reject")
def reject_action(approval_id: str):
    record = resolve(approval_id, "rejected")
    if not record:
        raise HTTPException(status_code=404, detail="Approval not found")
    audit.log_event(
        "owner_rejected",
        {
            "approval_id": approval_id,
            "domain": record.get("domain"),
            "task_type": record.get("task_type"),
            "input_preview": record.get("user_input", "")[:120],
        },
    )
    return {"status": "rejected", "record": record}


@router.post("/{approval_id}/execute")
def execute_action(approval_id: str):
    """
    Approve (if still pending) and execute the action in one shot.
    Idempotent: calling again on an already-executed record returns the existing result.
    """
    record = get_by_id(approval_id)
    if not record:
        raise HTTPException(status_code=404, detail="Approval not found")

    if record["status"] == EXECUTED:
        return record

    if record["status"] not in (PENDING, APPROVED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot execute approval with status '{record['status']}'",
        )

    # Auto-approve if still pending
    if record["status"] == PENDING:
        record = resolve(approval_id, "approved")

    session_id = record.get("session_id", "")
    audit.log_event("execution_requested", {"approval_id": approval_id}, session_id=session_id)

    execution_result = run_execution(
        user_input=record["user_input"],
        domain=record["domain"],
        task_type=record["task_type"],
        session_id=session_id,
    )

    updated = mark_executed(approval_id, execution_result)
    audit.log_event(
        "execution_completed",
        {"approval_id": approval_id, "success": execution_result["success"], "action_type": execution_result["action_type"]},
        session_id=session_id,
    )

    return updated
