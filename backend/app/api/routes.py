import json
import os
import signal
import subprocess
import time
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from app.approvals.store import get_pending
from app.audit import store as audit_store
from app.config import BACKEND_VERSION, GROQ_API_KEY, GROQ_MODEL, OLLAMA_MODEL, OLLAMA_URL, OPENROUTER_API_KEY, OPENROUTER_MODEL, PERPLEXITY_API_KEY, PERPLEXITY_MODEL
from app.memory.store import get_memory_stats
from app.orchestrator.engine import run_black, stream_black
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["Mr.Black"])


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
    return {"status": "ok", "service": "Mr.Black backend", "version": BACKEND_VERSION}


@router.get("/status")
def status():
    mem = get_memory_stats()
    return {
        "status": "MR.BLACK ONLINE",
        "phase": "v1.0",
        "mode": "local-first",
        "owner": "single-owner",
        "version": BACKEND_VERSION,
        "openrouter": {
            "configured": bool(OPENROUTER_API_KEY),
            "model": OPENROUTER_MODEL if OPENROUTER_API_KEY else None,
        },
        "groq": {
            "configured": bool(GROQ_API_KEY),
            "model": GROQ_MODEL if GROQ_API_KEY else None,
        },
        "perplexity": {
            "configured": bool(PERPLEXITY_API_KEY),
            "model": PERPLEXITY_MODEL if PERPLEXITY_API_KEY else None,
        },
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
    except Exception:
        import logging
        logging.getLogger(__name__).exception("chat endpoint error")
        raise HTTPException(status_code=500, detail="Internal error — check backend logs")


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


@router.post("/shutdown")
async def shutdown(background_tasks: BackgroundTasks):
    """Kill switch — shuts down all Mr. Black services. Triggered by 'Chibuike kill Mr. Black'."""
    audit_store.log_event("kill_switch_triggered", {"phrase": "Chibuike kill Mr. Black"})

    def _kill():
        time.sleep(0.3)
        subprocess.Popen(["pkill", "-f", "vite"], stderr=subprocess.DEVNULL)
        subprocess.Popen(["pkill", "-x", "ollama"], stderr=subprocess.DEVNULL)
        time.sleep(0.2)
        os.kill(os.getpid(), signal.SIGTERM)

    background_tasks.add_task(_kill)
    return {"status": "shutting_down", "message": "Mr. Black going offline. Goodbye."}
