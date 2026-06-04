import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Inference
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
OLLAMA_RETRIES = int(os.getenv("OLLAMA_RETRIES", "2"))

# Memory
MEMORY_PATH = Path(
    os.getenv(
        "MEMORY_PATH",
        str(Path(__file__).resolve().parents[1] / "black_memory.json"),
    )
)
MAX_CONVERSATIONS = int(os.getenv("MAX_CONVERSATIONS", "500"))
MAX_FACTS = int(os.getenv("MAX_FACTS", "50"))
CONVERSATION_WINDOW = int(os.getenv("CONVERSATION_WINDOW", "10"))
FACT_WINDOW = int(os.getenv("FACT_WINDOW", "10"))

# Security — empty string disables key check (local dev only)
BLACK_API_KEY = os.getenv("BLACK_API_KEY", "")

# Cloud inference fallback — used when Ollama is unreachable
# Leave ANTHROPIC_API_KEY empty to disable fallback (Ollama failures surface as errors)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "claude-haiku-4-5-20251001")

# CORS
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

AUDIT_LOG_PATH = Path(
    os.getenv(
        "AUDIT_LOG_PATH",
        str(Path(__file__).resolve().parents[1] / "black_audit.jsonl"),
    )
)

APPROVALS_PATH = Path(
    os.getenv(
        "APPROVALS_PATH",
        str(Path(__file__).resolve().parents[1] / "black_approvals.json"),
    )
)

# Finance domain — Alpha Vantage market data (free tier: 25 req/day, 5/min)
# Leave empty to disable live data injection (Finance Agent uses LLM knowledge only)
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# Memory encryption at rest — Fernet symmetric key (base64-encoded 32-byte key)
# Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Leave empty to store memory as plaintext (acceptable for local-only use)
MEMORY_ENCRYPTION_KEY = os.getenv("MEMORY_ENCRYPTION_KEY", "")

BACKEND_VERSION = "2.0.0"
