CURRENT_SCHEMA_VERSION = 1

DEFAULT_MEMORY: dict = {
    "schema_version": CURRENT_SCHEMA_VERSION,
    "user": {
        "name": "",
        "identity": "",
        "goals": [],
        "businesses": [],
        "projects": [],
        "preferences": {},
        "values": [],
    },
    "memories": [],
    "conversations": [],
}


def migrate(memory: dict) -> dict:
    version = memory.get("schema_version", 0)

    if version < 1:
        # v0 → v1: add schema_version and ensure all top-level keys exist
        memory["schema_version"] = 1
        memory.setdefault("user", DEFAULT_MEMORY["user"].copy())
        memory.setdefault("memories", [])
        memory.setdefault("conversations", [])
        user = memory["user"]
        user.setdefault("preferences", {})
        user.setdefault("values", [])

    # Future migrations: add `if version < 2:` blocks here

    return memory
