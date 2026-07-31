"""
Voice routes:
  POST /api/voice/transcribe  — receive audio blob, return transcribed text
                                 Primary: Groq Whisper-large-v3-turbo (free, ~1s, no cold start)
                                 Fallback: local OpenAI Whisper (no internet needed)
  POST /api/voice/speak       — speak text via macOS `say` command (TTS)
  GET  /api/voice/status      — check STT provider availability
"""
import os
import subprocess
import tempfile
from pathlib import Path

# Ensure Homebrew bin is in PATH so local Whisper can find ffmpeg
_HOMEBREW_BIN = "/opt/homebrew/bin"
if _HOMEBREW_BIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _HOMEBREW_BIN + ":" + os.environ.get("PATH", "")

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, GROQ_API_KEY, TTS_VOICE, WHISPER_MODEL

router = APIRouter(prefix="/api/voice", tags=["voice"])

_local_model = None  # lazy-loaded only if Groq fails or key not set


def _load_local_model():
    global _local_model
    if _local_model is None:
        import whisper
        _local_model = whisper.load_model(WHISPER_MODEL)
    return _local_model


def _groq_ready() -> bool:
    return bool(GROQ_API_KEY)


@router.get("/status")
def voice_status():
    """Report STT provider status."""
    groq_stt = _groq_ready()

    whisper_ok = False
    ffmpeg_ok = False
    try:
        import whisper  # noqa: F401
        whisper_ok = True
    except ImportError:
        pass

    _FFMPEG_PATHS = ["ffmpeg", "/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"]
    for _fp in _FFMPEG_PATHS:
        try:
            result = subprocess.run([_fp, "-version"], capture_output=True, timeout=5)
            if result.returncode == 0:
                ffmpeg_ok = True
                break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    elevenlabs_ok = bool(ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID)
    return {
        "stt_provider": "groq-whisper" if groq_stt else "local-whisper",
        "groq_whisper_available": groq_stt,
        "local_whisper_available": whisper_ok,
        "ffmpeg_available": ffmpeg_ok,
        "model": "whisper-large-v3-turbo" if groq_stt else WHISPER_MODEL,
        "tts_provider": "elevenlabs" if elevenlabs_ok else "macos",
        "tts_voice": "elevenlabs" if elevenlabs_ok else TTS_VOICE,
        "elevenlabs_configured": elevenlabs_ok,
        "ready": groq_stt or (whisper_ok and ffmpeg_ok),
    }


@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """
    Transcribe audio. Tries Groq Whisper API first (fast, free, no cold start).
    Falls back to local Whisper if Groq is unavailable or fails.
    """
    suffix = Path(audio.filename or "audio.webm").suffix or ".webm"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        # — Primary: Groq Whisper API —
        if _groq_ready():
            try:
                from app.services.groq_client import transcribe_audio
                text = transcribe_audio(tmp_path)
                return {"text": text, "provider": "groq-whisper", "language": "en"}
            except Exception:
                pass  # fall through to local Whisper

        # — Fallback: local Whisper —
        try:
            import whisper  # noqa: F401
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="No STT available: set GROQ_API_KEY or run `pip install openai-whisper`",
            )

        _ffmpeg_paths = ["ffmpeg", "/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"]
        if not any(
            subprocess.run([p, "-version"], capture_output=True).returncode == 0
            for p in _ffmpeg_paths
        ):
            raise HTTPException(status_code=503, detail="ffmpeg not found. Run: brew install ffmpeg")

        model = _load_local_model()
        result = model.transcribe(tmp_path, fp16=False)
        text = result.get("text", "").strip()
        return {"text": text, "provider": "local-whisper", "language": result.get("language", "unknown")}

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(exc)[:200]}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


class SpeakRequest(BaseModel):
    text: str
    voice: str = ""


@router.post("/speak")
def speak(body: SpeakRequest):
    """
    Speak text aloud.
    Primary: ElevenLabs (when ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID are set).
    Fallback: macOS `say` with configured TTS_VOICE.
    """
    text = body.text[:600].strip()
    if not text:
        return {"ok": True}

    # — Primary: ElevenLabs —
    if ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID:
        try:
            from app.services.elevenlabs_client import speak as el_speak
            audio_path = el_speak(text)
            subprocess.run(["afplay", str(audio_path)], check=False)
            audio_path.unlink(missing_ok=True)
            return {"ok": True, "provider": "elevenlabs"}
        except Exception:
            pass  # fall through to macOS say

    # — Fallback: macOS say —
    voice = body.voice.strip() or TTS_VOICE
    subprocess.run(["say", "-v", voice, text], check=False)
    return {"ok": True, "provider": "macos"}


@router.get("/greet")
def greet():
    """Return a time-aware, name-aware Jarvis-style greeting."""
    import random
    from datetime import datetime

    from app.memory.store import load_memory

    hour = datetime.now().hour

    try:
        data = load_memory()
        name = (data.get("user", {}).get("name") or "").strip()
    except Exception:
        name = ""

    n = f", {name}" if name else ""

    if 5 <= hour < 12:
        options = [
            f"Good morning{n}. What are we working on today?",
            f"Morning{n}. Systems ready. Go ahead.",
            f"Good morning{n}. Ready when you are.",
            f"Morning{n}. What do you need?",
            f"Good morning{n}. I'm listening.",
        ]
    elif 12 <= hour < 17:
        options = [
            f"Good afternoon{n}. What are we tackling?",
            f"Afternoon{n}. I'm here.",
            f"Good afternoon{n}. What do you need?",
            f"Afternoon{n}. Go ahead.",
            f"Good afternoon{n}. I'm listening.",
        ]
    elif 17 <= hour < 21:
        options = [
            f"Good evening{n}. What's on your mind?",
            f"Evening{n}. I'm listening.",
            f"Good evening{n}. What do you need?",
            f"Evening{n}. Go ahead.",
        ]
    else:
        options = [
            f"Still up{n}? What do you need?",
            f"Late night{n}. I'm here.",
            f"Working late{n}? What's on your mind?",
            f"Can't sleep{n}? Go ahead.",
        ]

    return {"greeting": random.choice(options), "hour": hour}
