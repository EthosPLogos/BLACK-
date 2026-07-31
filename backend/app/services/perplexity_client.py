"""
Perplexity API client — OpenAI-compatible chat completions.
Sonar models include live web search on every query.
"""
import json
from typing import AsyncIterator

import httpx

from app.config import PERPLEXITY_API_KEY, PERPLEXITY_MODEL

_BASE = "https://api.perplexity.ai"
_TIMEOUT = 60


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }


def _build_messages(prompt: str, system: str) -> list[dict]:
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return msgs


def call_perplexity(prompt: str, system: str = "") -> str:
    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": _build_messages(prompt, system),
    }
    resp = httpx.post(
        f"{_BASE}/chat/completions",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


async def stream_perplexity(prompt: str, system: str = "") -> AsyncIterator[str]:
    payload = {
        "model": PERPLEXITY_MODEL,
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
