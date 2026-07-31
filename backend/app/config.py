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
CONVERSATION_WINDOW = int(os.getenv("CONVERSATION_WINDOW", "6"))
FACT_WINDOW = int(os.getenv("FACT_WINDOW", "8"))

# Security — empty string disables key check (dev mode).
# WARNING: without a key, the entire API is open to anyone on the network.
# Generate a key: python -c "import secrets; print(secrets.token_hex(32))"
BLACK_API_KEY = os.getenv("BLACK_API_KEY", "")
if not BLACK_API_KEY:
    import warnings
    warnings.warn(
        "\n\n  ⚠  BLACK_API_KEY is not set — authentication is DISABLED.\n"
        "     Anyone on your network can reach the API.\n"
        "     Set BLACK_API_KEY in .env to lock it down.\n"
        "     Generate: python -c \"import secrets; print(secrets.token_hex(32))\"\n",
        stacklevel=1,
    )

# OpenRouter — primary cloud inference (free models, no billing on :free tier)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

# Groq — second tier (free, very fast, generous rate limits)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Perplexity — last resort (paid per query, live web search)
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar")

# Anthropic — Sonnet for frontier reasoning tier, Haiku as last-resort fallback
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
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

# Voice — Whisper STT + TTS
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
TTS_VOICE = os.getenv("TTS_VOICE", "Daniel")          # macOS fallback voice (British male)

# ElevenLabs TTS — primary voice when configured
# Get key: elevenlabs.io → Profile → API Key
# Pick voice: elevenlabs.io/voice-library → search "African British" → copy voice ID
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

SCHEDULE_PATH = Path(
    os.getenv(
        "SCHEDULE_PATH",
        str(Path(__file__).resolve().parents[1] / "black_schedule.json"),
    )
)

# Personal Integrations — directories BLACK can search for files
# Comma-separated absolute or ~ paths. Defaults to Desktop + Documents + Downloads.
# Weather — city name or zip code. Leave empty to auto-detect by IP.
WEATHER_LOCATION = os.getenv("WEATHER_LOCATION", "")

FILE_SEARCH_PATHS: list[str] = [
    p.strip()
    for p in os.getenv(
        "FILE_SEARCH_PATHS",
        "~/Desktop,~/Documents,~/Downloads",
    ).split(",")
    if p.strip()
]

# Email — IMAP read-only access (iCloud by default)
# iCloud: imap.mail.me.com | Gmail: imap.gmail.com | Outlook: outlook.office365.com
# Requires an App-Specific Password — not your Apple ID password.
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = os.getenv("EMAIL_PORT", "993")
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FOLDER = os.getenv("EMAIL_FOLDER", "INBOX")

# Alpaca — real-time market data + brokerage (paper trading by default)
# Create free account at alpaca.markets → API Keys → generate Paper key pair
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_LIVE = os.getenv("ALPACA_LIVE", "false").lower() == "true"

# Shopify — ecommerce store data (read-only Custom App)
# Store Admin → Settings → Apps → Develop apps → Create app → API credentials
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL", "")   # yourstore.myshopify.com
SHOPIFY_API_TOKEN = os.getenv("SHOPIFY_API_TOKEN", "")

# Email SMTP — sending via same credentials as IMAP
# iCloud default: smtp.mail.me.com:587 with App-Specific Password
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp.mail.me.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))

# Job Apply Agent
APPLICATIONS_PATH = Path(
    os.getenv("APPLICATIONS_PATH",
              str(Path(__file__).resolve().parents[1] / "black_applications.json"))
)
JOB_APPLY_CONFIG_PATH = Path(
    os.getenv("JOB_APPLY_CONFIG_PATH",
              str(Path(__file__).resolve().parents[1] / "black_job_criteria.json"))
)
JOB_RESUMES_DIR = Path(
    os.getenv("JOB_RESUMES_DIR",
              str(Path(__file__).resolve().parents[1] / "job_resumes"))
)

BACKEND_VERSION = "1.0.0"
