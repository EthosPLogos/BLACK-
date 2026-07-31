"""
ElevenLabs TTS client.
Streams audio directly to a temp file, then hands the path back
so voice_routes.py can play it with afplay (non-blocking).
"""
import tempfile
from pathlib import Path

import httpx

from app.config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

_BASE = "https://api.elevenlabs.io/v1"
_MODEL = "eleven_multilingual_v2"


def is_configured() -> bool:
    return bool(ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID)


def speak(text: str, stability: float = 0.5, similarity_boost: float = 0.8) -> Path:
    """
    Synthesise text → returns path to a temporary .mp3 file.
    Caller is responsible for deleting the file after playback.
    """
    if not is_configured():
        raise RuntimeError("ElevenLabs not configured — set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in .env")

    url = f"{_BASE}/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": _MODEL,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": 0.4,
            "use_speaker_boost": True,
        },
    }

    with httpx.stream("POST", url, json=payload, headers=headers, timeout=30) as resp:
        resp.raise_for_status()
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        for chunk in resp.iter_bytes(chunk_size=4096):
            tmp.write(chunk)
        tmp.flush()
        return Path(tmp.name)
