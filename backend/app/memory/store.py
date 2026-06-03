import json
from pathlib import Path
from datetime import datetime

MEMORY_PATH = Path(__file__).resolve().parents[2] / "black_memory.json"


DEFAULT_MEMORY = {
    "user": {
        "name": "",
        "identity": "",
        "goals": [],
        "businesses": [],
        "projects": [],
        "preferences": {},
        "values": []
    },
    "memories": [],
    "conversations": []
}


def load_memory() -> dict:
    if not MEMORY_PATH.exists():
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY

    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY


def save_memory(memory: dict) -> None:
    with open(MEMORY_PATH, "w", encoding="utf-8") as file:
        json.dump(memory, file, ensure_ascii=False, indent=2)


def get_user_context() -> str:
    memory = load_memory()
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

    facts = memory.get("memories", [])[-5:]
    for item in facts:
        fact = item.get("fact")
        if fact:
            lines.append(f"Memory: {fact}")

    return "\n".join(lines) if lines else "No stored user context yet."


def add_conversation(user_message: str, black_reply: str) -> None:
    memory = load_memory()
    memory["conversations"].append({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user": user_message,
        "assistant": black_reply,
    })
    save_memory(memory)