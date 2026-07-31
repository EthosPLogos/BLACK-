"""
OpenRouter API client — OpenAI-compatible, aggregates hundreds of models.
Free-tier models (e.g. llama-3.3-70b:free) incur no billing.
"""
import json
from typing import AsyncIterator

import httpx

from app.config import OPENROUTER_API_KEY, OPENROUTER_MODEL

_BASE = "https://openrouter.ai/api/v1"
_TIMEOUT = 60


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "Mr.Black",
    }


def _build_messages(prompt: str, system: str) -> list[dict]:
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return msgs


def call_openrouter(prompt: str, system: str = "") -> str:
    import time
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": _build_messages(prompt, system),
    }
    for attempt in range(2):
        resp = httpx.post(
            f"{_BASE}/chat/completions",
            json=payload,
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if resp.status_code == 429 and attempt == 0:
            time.sleep(5)
            continue
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    resp.raise_for_status()  # re-raise after exhausted retries


async def stream_openrouter(prompt: str, system: str = "") -> AsyncIterator[str]:
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": _build_messages(prompt, system),
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        async with client.stream(
            "POST",
            f"{_BASE}/chat/completions",
            json=payload,
            headers=_headers(),
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
