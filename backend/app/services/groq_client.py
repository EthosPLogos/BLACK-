"""
Groq API client — OpenAI-compatible, extremely fast inference.
Free tier has generous rate limits. Runs Llama 3.3 70B at full speed.
Also provides Whisper-large-v3-turbo for STT — faster than local Whisper with no cold-start.
"""
import json
from pathlib import Path
from typing import AsyncIterator

import httpx

from app.config import GROQ_API_KEY, GROQ_MODEL

_GROQ_WHISPER_MODEL = "whisper-large-v3-turbo"

_BASE = "https://api.groq.com/openai/v1"
_TIMEOUT = 60


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }


def transcribe_audio(file_path: str | Path, language: str = "en") -> str:
    """
    Transcribe audio via Groq Whisper-large-v3-turbo.
    Faster than local Whisper — no model load, no GPU needed, ~1-2s for typical clips.
    Raises httpx.HTTPStatusError on API error so caller can fall back to local Whisper.
    Supported formats: webm, mp3, mp4, m4a, ogg, wav, flac (max 25 MB).
    """
    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    suffix = Path(file_path).suffix.lower().lstrip(".") or "webm"
    mime = {
        "webm": "audio/webm",
        "mp3": "audio/mpeg",
        "mp4": "audio/mp4",
        "m4a": "audio/mp4",
        "ogg": "audio/ogg",
        "wav": "audio/wav",
        "flac": "audio/flac",
    }.get(suffix, "audio/webm")

    resp = httpx.post(
        f"{_BASE}/audio/transcriptions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        files={"file": (Path(file_path).name, audio_bytes, mime)},
        data={"model": _GROQ_WHISPER_MODEL, "language": language, "response_format": "text"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text.strip()


def _build_messages(prompt: str, system: str) -> list[dict]:
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return msgs


def call_groq(prompt: str, system: str = "") -> str:
    payload = {
        "model": GROQ_MODEL,
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


async def stream_groq(prompt: str, system: str = "") -> AsyncIterator[str]:
    payload = {
        "model": GROQ_MODEL,
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
