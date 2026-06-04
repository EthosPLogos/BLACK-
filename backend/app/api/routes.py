import json
import time
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from app.approvals.store import get_pending
from app.audit import store as audit_store
from app.config import BACKEND_VERSION, OLLAMA_MODEL, OLLAMA_URL
from app.memory.store import get_memory_stats
from app.orchestrator.engine import run_black, stream_black
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["BLACK"])


def _probe_ollama() -> dict:
    base = f"{urlparse(OLLAMA_URL).scheme}://{urlparse(OLLAMA_URL).netloc}"
    try:
        t0 = time.time()
        r = httpx.get(f"{base}/api/tags", timeout=3.0)
        latency_ms = round((time.time() - t0) * 1000)
        if r.status_code == 200:
            return {"status": "ok", "model": OLLAMA_MODEL, "latency_ms": latency_ms}
        return {"status": "degraded", "model": OLLAMA_MODEL, "error": f"HTTP {r.status_code}"}
    except Exception as exc:
        return {"status": "unreachable", "model": OLLAMA_MODEL, "error": str(exc)[:120]}


@router.get("/health")
def health():
    return {"status": "ok", "service": "BLACK backend", "version": BACKEND_VERSION}


@router.get("/status")
def status():
    mem = get_memory_stats()
    return {
        "status": "BLACK ONLINE",
        "phase": "Phase 2",
        "mode": "local-first",
        "owner": "single-owner",
        "version": BACKEND_VERSION,
        "ollama": _probe_ollama(),
        "memory": mem,
        "audit": {"total_records": audit_store.count()},
        "approvals": {"pending": len(get_pending())},
    }


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, background_tasks: BackgroundTasks):
    try:
        result = run_black(payload.message, background_tasks=background_tasks)
        return ChatResponse(
            reply=result["reply"],
            agent=result["agent"],
            task_type=result["task_type"],
            memory_used=result["memory_used"],
            policy_verdict=result.get("policy_verdict", "auto_approved"),
            approval_id=result.get("approval_id"),
            inference_provider=result.get("inference_provider", "local"),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/chat/stream")
async def chat_stream(payload: ChatRequest):
    """
    SSE streaming endpoint. Yields token events so the owner sees output as it
    arrives from the model instead of waiting for the full response.

    Event types:
      token           — {"type": "token", "content": "<text>"}
      done            — {"type": "done", "agent": ..., "task_type": ..., ...}
      blocked         — {"type": "blocked", "reply": ..., "policy_verdict": "blocked"}
      pending_approval— {"type": "pending_approval", "reply": ..., "policy_verdict": ...}
      error           — {"type": "error", "content": "<message>"}
    """
    async def generate():
        async for event in stream_black(payload.message):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
