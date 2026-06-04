from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.audit import logger as audit
from app.memory.store import (
    add_fact,
    clear_conversations,
    get_memory_stats,
    load_memory,
    update_user_field,
)

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("")
def get_memory():
    memory = load_memory()
    return {
        "user": memory.get("user", {}),
        "facts": memory.get("memories", []),
        "conversation_count": len(memory.get("conversations", [])),
        "recent_conversations": memory.get("conversations", [])[-10:],
        "schema_version": memory.get("schema_version", 0),
    }


@router.get("/stats")
def get_stats():
    return get_memory_stats()


class AddFactRequest(BaseModel):
    fact: str


@router.post("/facts")
def post_fact(payload: AddFactRequest):
    if not payload.fact.strip():
        raise HTTPException(status_code=400, detail="Fact cannot be empty")
    add_fact(payload.fact.strip())
    audit.log_event("memory_fact_added", {"fact_preview": payload.fact[:80]})
    return {"ok": True}


@router.delete("/conversations")
def delete_conversations():
    clear_conversations()
    audit.log_event("conversations_cleared", {})
    return {"ok": True}


class UpdateUserRequest(BaseModel):
    field: str
    value: Any


@router.patch("/user")
def patch_user(payload: UpdateUserRequest):
    try:
        update_user_field(payload.field, payload.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    audit.log_event("user_profile_updated", {"field": payload.field})
    return {"ok": True}
