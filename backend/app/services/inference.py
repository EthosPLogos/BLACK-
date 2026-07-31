"""
Unified inference layer — tier-based model routing.

Three tiers selected automatically by query complexity and domain:

  frontier  — Claude Sonnet → Groq → OpenRouter
              Used for: finance analysis, code generation, long drafts, complex reasoning
              Rationale: highest reasoning quality where it matters; pays per query

  research  — Perplexity → Claude Sonnet → Groq
              Used for: web-dependent queries (world_intel, job_search, web domain)
              Rationale: Perplexity has live web search on every call; Sonnet synthesizes fallback

  fast      — Groq → OpenRouter → Ollama → Claude Haiku
              Used for: everything else — simple Q&A, calendar, weather, notes
              Rationale: free, instant, good enough for low-complexity queries
"""
import asyncio
import subprocess
import time
from typing import AsyncIterator, Literal

from app.config import GROQ_API_KEY, OPENROUTER_API_KEY, PERPLEXITY_API_KEY, ANTHROPIC_API_KEY
from app.services.anthropic_client import (
    call_claude,
    call_claude_frontier,
    stream_claude,
    stream_claude_frontier,
)
from app.services.groq_client import call_groq, stream_groq
from app.services.ollama_client import (
    call_ollama,
    invalidate_probe_cache,
    is_ollama_available,
    stream_ollama,
)
from app.services.openrouter_client import call_openrouter, stream_openrouter
from app.services.perplexity_client import call_perplexity, stream_perplexity

Tier = Literal["fast", "frontier", "research"]

_OLLAMA_RETRIES = 3
_OLLAMA_RETRY_DELAY = 2.0


class OllamaDownError(RuntimeError):
    pass


# ── availability checks ────────────────────────────────────────────────────────

def _groq_ready() -> bool:
    return bool(GROQ_API_KEY)

def _openrouter_ready() -> bool:
    return bool(OPENROUTER_API_KEY)

def _perplexity_ready() -> bool:
    return bool(PERPLEXITY_API_KEY)

def _anthropic_ready() -> bool:
    return bool(ANTHROPIC_API_KEY)


# ── tier selection ─────────────────────────────────────────────────────────────

def select_tier(task_type: str, domain: str, user_input: str) -> Tier:
    """
    Choose inference tier based on domain and query characteristics.
    Frontier costs money — only when complexity justifies it.
    Research uses Perplexity for live web — only when currency matters.
    """
    # Research domains — live web is the primary value
    if domain in ("web", "world_intel", "job_search"):
        return "research"

    # Finance — always frontier: wrong analysis has real financial consequences
    if domain == "finance":
        return "frontier"

    # Science — always frontier: depth and accuracy of scientific reasoning matters
    if domain == "science":
        return "frontier"

    # Security — always frontier: wrong threat assessment has real consequences
    if domain == "security":
        return "frontier"

    # GRE — frontier: adaptive coaching and diagnostic reasoning requires max quality
    if domain == "gre":
        return "frontier"

    # Forge — frontier: website generation needs max code quality
    if domain == "forge":
        return "frontier"

    # Code generation — frontier for non-trivial queries
    if domain == "build" and len(user_input) > 60:
        return "frontier"

    # Long drafts and action plans — worth the frontier quality
    if task_type in ("draft", "action-plan") and len(user_input) > 100:
        return "frontier"

    # Complex research queries
    if task_type == "research" and len(user_input) > 80:
        return "frontier"

    return "fast"


def active_provider(tier: Tier = "fast") -> str:
    if tier == "frontier":
        if _anthropic_ready():
            return "claude"
        if _groq_ready():
            return "groq"
    elif tier == "research":
        if _perplexity_ready():
            return "perplexity"
        if _anthropic_ready():
            return "claude"
        if _groq_ready():
            return "groq"
    else:
        if _groq_ready():
            return "groq"
        if _openrouter_ready():
            return "openrouter"
        if is_ollama_available():
            return "local"
        if _anthropic_ready():
            return "claude-haiku"
    return "none"


# ── Ollama resilience ──────────────────────────────────────────────────────────

def _confirm_ollama_down() -> bool:
    for _ in range(_OLLAMA_RETRIES):
        invalidate_probe_cache()
        if is_ollama_available():
            return False
        time.sleep(_OLLAMA_RETRY_DELAY)
    return True


async def _confirm_ollama_down_async() -> bool:
    for _ in range(_OLLAMA_RETRIES):
        invalidate_probe_cache()
        if is_ollama_available():
            return False
        await asyncio.sleep(_OLLAMA_RETRY_DELAY)
    return True


def _ollama_alert():
    try:
        subprocess.run(
            ["osascript", "-e",
             'display alert "Mr.Black — All providers failed" message '
             '"All inference providers are unavailable." '
             'buttons {"OK"} default button "OK" as critical'],
            capture_output=True, text=True, check=False, timeout=30,
        )
    except Exception:
        pass


# ── sync inference ─────────────────────────────────────────────────────────────

def call_inference(
    prompt: str,
    system: str = "",
    tier: Tier = "fast",
) -> tuple[str, str]:
    """
    Synchronous inference with tier-based model routing.
    Returns (reply, provider_str).
    """
    if tier == "frontier":
        if _anthropic_ready():
            try:
                return call_claude_frontier(prompt, system), "claude-sonnet"
            except Exception:
                pass
        if _groq_ready():
            try:
                return call_groq(prompt, system), "groq"
            except Exception:
                pass
        if _openrouter_ready():
            try:
                return call_openrouter(prompt, system), "openrouter"
            except Exception:
                pass

    elif tier == "research":
        if _perplexity_ready():
            try:
                return call_perplexity(prompt, system), "perplexity"
            except Exception:
                pass
        if _anthropic_ready():
            try:
                return call_claude_frontier(prompt, system), "claude-sonnet"
            except Exception:
                pass
        if _groq_ready():
            try:
                return call_groq(prompt, system), "groq"
            except Exception:
                pass

    else:  # fast
        if _groq_ready():
            try:
                return call_groq(prompt, system), "groq"
            except Exception:
                pass
        if _openrouter_ready():
            try:
                return call_openrouter(prompt, system), "openrouter"
            except Exception:
                pass
        if is_ollama_available():
            try:
                return call_ollama(prompt, system), "local"
            except Exception:
                invalidate_probe_cache()
        if not _confirm_ollama_down():
            try:
                return call_ollama(prompt, system), "local"
            except Exception:
                pass

    # Universal last resort — Claude Haiku (cheap, always available if key exists)
    if _anthropic_ready():
        try:
            return call_claude(prompt, system), "claude-haiku"
        except Exception:
            pass

    _ollama_alert()
    raise OllamaDownError("All inference providers are unavailable.")


# ── async streaming inference ──────────────────────────────────────────────────

async def stream_inference(
    prompt: str,
    system: str = "",
    tier: Tier = "fast",
) -> AsyncIterator[str]:
    """
    Async streaming inference with tier-based model routing.
    Yields string tokens.
    """
    if tier == "frontier":
        if _anthropic_ready():
            try:
                async for token in stream_claude_frontier(prompt, system):
                    yield token
                return
            except Exception:
                pass
        if _groq_ready():
            try:
                async for token in stream_groq(prompt, system):
                    yield token
                return
            except Exception:
                pass
        if _openrouter_ready():
            try:
                async for token in stream_openrouter(prompt, system):
                    yield token
                return
            except Exception:
                pass

    elif tier == "research":
        if _perplexity_ready():
            try:
                async for token in stream_perplexity(prompt, system):
                    yield token
                return
            except Exception:
                pass
        if _anthropic_ready():
            try:
                async for token in stream_claude_frontier(prompt, system):
                    yield token
                return
            except Exception:
                pass
        if _groq_ready():
            try:
                async for token in stream_groq(prompt, system):
                    yield token
                return
            except Exception:
                pass

    else:  # fast
        if _groq_ready():
            try:
                async for token in stream_groq(prompt, system):
                    yield token
                return
            except Exception:
                pass
        if _openrouter_ready():
            try:
                async for token in stream_openrouter(prompt, system):
                    yield token
                return
            except Exception:
                pass
        if is_ollama_available():
            try:
                async for token in stream_ollama(prompt, system):
                    yield token
                return
            except Exception:
                invalidate_probe_cache()
        if not await _confirm_ollama_down_async():
            try:
                async for token in stream_ollama(prompt, system):
                    yield token
                return
            except Exception:
                pass

    # Universal last resort — Claude Haiku
    if _anthropic_ready():
        try:
            async for token in stream_claude(prompt, system):
                yield token
            return
        except Exception:
            pass

    await asyncio.to_thread(_ollama_alert)
    raise OllamaDownError("All inference providers are unavailable.")
