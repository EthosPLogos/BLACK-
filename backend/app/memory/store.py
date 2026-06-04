import json
from datetime import datetime, timezone

from app.config import (
    CONVERSATION_WINDOW,
    FACT_WINDOW,
    MAX_CONVERSATIONS,
    MAX_FACTS,
    MEMORY_PATH,
)
from app.memory import crypto
from app.memory.models import DEFAULT_MEMORY, migrate


def load_memory() -> dict:
    if not MEMORY_PATH.exists():
        save_memory(DEFAULT_MEMORY.copy())
        return DEFAULT_MEMORY.copy()

    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError:
        save_memory(DEFAULT_MEMORY.copy())
        return DEFAULT_MEMORY.copy()

    # Detect encrypted wrapper format {"__encrypted__": true, "data": "..."}
    was_encrypted = raw.get("__encrypted__", False)
    if was_encrypted:
        memory = json.loads(crypto.decrypt(raw["data"]))
    else:
        memory = raw

    memory = migrate(memory)

    # Auto-encrypt: key is now set but the file was still plaintext → re-save
    if not was_encrypted and crypto.is_enabled():
        save_memory(memory)

    return memory


def save_memory(memory: dict) -> None:
    if crypto.is_enabled():
        plaintext = json.dumps(memory, ensure_ascii=False, indent=2)
        wrapper = {"__encrypted__": True, "data": crypto.encrypt(plaintext)}
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(wrapper, f)
    else:
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)


def _format_user_context(memory: dict) -> str:
    user = memory.get("user", {})
    lines = []

    if user.get("name"):
        lines.append(f"Name: {user['name']}")
    if user.get("identity"):
        lines.append(f"Identity: {user['identity']}")
    if user.get("goals"):
        lines.append("Goals: " + "; ".join(user["goals"]))
    if user.get("businesses"):
        lines.append("Businesses: " + "; ".join(user["businesses"]))
    if user.get("projects"):
        lines.append("Projects: " + "; ".join(user["projects"]))
    if user.get("values"):
        lines.append("Values: " + "; ".join(user["values"]))

    for item in memory.get("memories", [])[-FACT_WINDOW:]:
        fact = item.get("fact")
        if fact:
            lines.append(f"Memory: {fact}")

    return "\n".join(lines) if lines else "No stored user context yet."


def get_user_context() -> str:
    return _format_user_context(load_memory())


def get_context_bundle() -> tuple[str, list[dict]]:
    """Load memory once and return (user_context_string, conversation_window)."""
    memory = load_memory()
    return _format_user_context(memory), memory.get("conversations", [])[-CONVERSATION_WINDOW:]


def get_conversation_window() -> list[dict]:
    memory = load_memory()
    return memory.get("conversations", [])[-CONVERSATION_WINDOW:]


_ALLOWED_USER_FIELDS = {"name", "identity", "goals", "businesses", "projects", "values"}


def get_memory_stats() -> dict:
    memory = load_memory()
    user = memory.get("user", {})
    filled = sum(1 for f in _ALLOWED_USER_FIELDS if user.get(f))
    return {
        "schema_version": memory.get("schema_version", 0),
        "fact_count": len(memory.get("memories", [])),
        "conversation_count": len(memory.get("conversations", [])),
        "profile_fields_filled": f"{filled}/{len(_ALLOWED_USER_FIELDS)}",
        "encrypted": crypto.is_enabled(),
    }


def add_fact(fact: str) -> None:
    memory = load_memory()
    memory.setdefault("memories", []).append(
        {"fact": fact, "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    if len(memory["memories"]) > MAX_FACTS:
        memory["memories"] = memory["memories"][-MAX_FACTS:]
    save_memory(memory)


def clear_conversations() -> None:
    memory = load_memory()
    memory["conversations"] = []
    save_memory(memory)


def update_user_field(field: str, value) -> None:
    if field not in _ALLOWED_USER_FIELDS:
        raise ValueError(f"Unknown user field: {field!r}")
    memory = load_memory()
    memory["user"][field] = value
    save_memory(memory)


def add_conversation(user_message: str, black_reply: str) -> None:
    memory = load_memory()
    memory["conversations"].append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user_message,
            "assistant": black_reply,
        }
    )
    if len(memory["conversations"]) > MAX_CONVERSATIONS:
        memory["conversations"] = memory["conversations"][-MAX_CONVERSATIONS:]
    if len(memory.get("memories", [])) > MAX_FACTS:
        memory["memories"] = memory["memories"][-MAX_FACTS:]

    save_memory(memory)
