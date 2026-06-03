from fastapi import APIRouter, HTTPException

from app.orchestrator.engine import run_black
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["BLACK"])


@router.get("/status")
def status():
    return {
        "status": "BLACK ONLINE",
        "phase": "Local Phase 1",
        "mode": "local-first",
        "owner": "single-owner",
    }


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    try:
        result = run_black(payload.message)
        return ChatResponse(
            reply=result["reply"],
            agent=result["agent"],
            task_type=result["task_type"],
            memory_used=result["memory_used"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))