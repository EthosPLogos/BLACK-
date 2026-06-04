from typing import AsyncIterator

import anthropic

from app.config import ANTHROPIC_API_KEY, FALLBACK_MODEL

# Lazy singletons — only instantiated if fallback is actually triggered.
_sync_client: anthropic.Anthropic | None = None
_async_client: anthropic.AsyncAnthropic | None = None


def _get_sync() -> anthropic.Anthropic:
    global _sync_client
    if _sync_client is None:
        _sync_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _sync_client


def _get_async() -> anthropic.AsyncAnthropic:
    global _async_client
    if _async_client is None:
        _async_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    return _async_client


def call_claude(prompt: str, system: str = "") -> str:
    """Synchronous Claude inference — mirrors call_ollama interface."""
    kwargs: dict = {
        "model": FALLBACK_MODEL,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    msg = _get_sync().messages.create(**kwargs)
    return msg.content[0].text


async def stream_claude(prompt: str, system: str = "") -> AsyncIterator[str]:
    """Async streaming Claude inference — mirrors stream_ollama interface."""
    kwargs: dict = {
        "model": FALLBACK_MODEL,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    async with _get_async().messages.stream(**kwargs) as stream:
        async for text in stream.text_stream:
            if text:
                yield text
