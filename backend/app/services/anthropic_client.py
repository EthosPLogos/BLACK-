from typing import AsyncIterator

import anthropic

from app.config import ANTHROPIC_API_KEY, CLAUDE_MODEL, FALLBACK_MODEL

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


def _call(model: str, prompt: str, system: str) -> str:
    kwargs: dict = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    return _get_sync().messages.create(**kwargs).content[0].text


async def _stream(model: str, prompt: str, system: str) -> AsyncIterator[str]:
    kwargs: dict = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    async with _get_async().messages.stream(**kwargs) as stream:
        async for text in stream.text_stream:
            if text:
                yield text


# Frontier tier — Claude Sonnet (complex reasoning, code, finance)
def call_claude_frontier(prompt: str, system: str = "") -> str:
    return _call(CLAUDE_MODEL, prompt, system)


async def stream_claude_frontier(prompt: str, system: str = "") -> AsyncIterator[str]:
    async for token in _stream(CLAUDE_MODEL, prompt, system):
        yield token


# Fallback tier — Claude Haiku (last-resort, cheap)
def call_claude(prompt: str, system: str = "") -> str:
    return _call(FALLBACK_MODEL, prompt, system)


async def stream_claude(prompt: str, system: str = "") -> AsyncIterator[str]:
    async for token in _stream(FALLBACK_MODEL, prompt, system):
        yield token
