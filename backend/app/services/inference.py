"""
Unified inference layer.

Call order:
  1. Probe Ollama availability (cached 30s — no extra round-trip if healthy).
  2. If available → use Ollama.  On connection failure → invalidate cache, fall through.
  3. If fallback is configured (ANTHROPIC_API_KEY set) → use Claude.
  4. If neither works → raise RuntimeError.

Callers use:
  call_inference(prompt, system)          → (reply, provider)
  stream_inference(prompt, system)        → AsyncIterator[str]  (tokens only)
  active_provider()                       → "local" | "cloud"
"""
from typing import AsyncIterator

from app.config import ANTHROPIC_API_KEY
from app.services.anthropic_client import call_claude, stream_claude
from app.services.ollama_client import (
    call_ollama,
    invalidate_probe_cache,
    is_ollama_available,
    stream_ollama,
)


def _fallback_ready() -> bool:
    return bool(ANTHROPIC_API_KEY)


def _no_fallback_error() -> RuntimeError:
    return RuntimeError(
        "Ollama is unreachable and no ANTHROPIC_API_KEY is configured. "
        "Set ANTHROPIC_API_KEY in backend/.env to enable cloud fallback."
    )


def active_provider() -> str:
    """Return which provider will be used for the next inference call."""
    if is_ollama_available():
        return "local"
    if _fallback_ready():
        return "cloud"
    return "local"  # will fail at inference time with a clear error


def call_inference(prompt: str, system: str = "") -> tuple[str, str]:
    """
    Synchronous inference with automatic fallback.
    Returns (reply, provider) where provider is 'local' or 'cloud'.
    """
    if is_ollama_available():
        try:
            return call_ollama(prompt, system), "local"
        except RuntimeError as exc:
            if "not reachable" in str(exc):
                invalidate_probe_cache()
            else:
                raise

    if not _fallback_ready():
        raise _no_fallback_error()

    return call_claude(prompt, system), "cloud"


async def stream_inference(prompt: str, system: str = "") -> AsyncIterator[str]:
    """
    Async streaming inference with automatic fallback.
    Yields tokens. Caller uses active_provider() to know which provider is running.
    """
    if is_ollama_available():
        try:
            async for token in stream_ollama(prompt, system):
                yield token
            return
        except RuntimeError as exc:
            if "not reachable" in str(exc):
                invalidate_probe_cache()
            else:
                raise

    if not _fallback_ready():
        raise _no_fallback_error()

    async for token in stream_claude(prompt, system):
        yield token
