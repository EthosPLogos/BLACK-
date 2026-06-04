import json
import time
from typing import AsyncIterator
from urllib.parse import urlparse

import httpx

from app.config import OLLAMA_MODEL, OLLAMA_RETRIES, OLLAMA_TIMEOUT, OLLAMA_URL

# Persistent sync client — reuses TCP connection across requests (avoids
# per-request handshake overhead to Ollama). Keepalive expiry set to 30s.
_sync_client = httpx.Client(
    timeout=OLLAMA_TIMEOUT,
    limits=httpx.Limits(
        max_connections=5,
        max_keepalive_connections=2,
        keepalive_expiry=30,
    ),
)


# ── Availability probe ─────────────────────────────────────────────────────────
# Result is cached for 30s so we don't add a round-trip on every inference call.
# Invalidated explicitly when a live inference call fails with a connection error.

_PROBE_TTL = 30.0
_probe_cache: dict = {"time": 0.0, "result": True}


def is_ollama_available() -> bool:
    now = time.time()
    if now - _probe_cache["time"] < _PROBE_TTL:
        return _probe_cache["result"]
    base = f"{urlparse(OLLAMA_URL).scheme}://{urlparse(OLLAMA_URL).netloc}"
    try:
        r = httpx.get(f"{base}/api/tags", timeout=3.0)
        result = r.status_code == 200
    except Exception:
        result = False
    _probe_cache["time"] = now
    _probe_cache["result"] = result
    return result


def invalidate_probe_cache() -> None:
    """Force the next is_ollama_available() call to re-probe."""
    _probe_cache["time"] = 0.0


def call_ollama(prompt: str, system: str = "") -> str:
    """Synchronous inference call — used by chain runner and verifier."""
    payload: dict = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system

    last_error = "Ollama request failed"

    for _ in range(OLLAMA_RETRIES + 1):
        try:
            response = _sync_client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            return response.json().get("response", "").strip()

        except httpx.ConnectError:
            raise RuntimeError(
                "Ollama is not reachable — confirm it is running on "
                f"{OLLAMA_URL.split('/api')[0]}"
            )

        except httpx.TimeoutException:
            last_error = f"Ollama timed out after {OLLAMA_TIMEOUT}s"

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama returned HTTP {exc.response.status_code}: "
                f"{exc.response.text[:200]}"
            )

    raise RuntimeError(last_error)


async def stream_ollama(prompt: str, system: str = "") -> AsyncIterator[str]:
    """
    Async streaming inference — yields tokens as they arrive from Ollama.
    Used by the /api/chat/stream endpoint so the owner sees output immediately
    instead of waiting for the full response.
    """
    payload: dict = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": True}
    if system:
        payload["system"] = system

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            async with client.stream("POST", OLLAMA_URL, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done"):
                        return

    except httpx.ConnectError:
        raise RuntimeError(
            "Ollama is not reachable — confirm it is running on "
            f"{OLLAMA_URL.split('/api')[0]}"
        )
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Ollama returned HTTP {exc.response.status_code}: "
            f"{exc.response.text[:200]}"
        )
