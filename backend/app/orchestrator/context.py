from app.memory.store import get_context_bundle

_NO_CONTEXT = "No stored user context yet."


def build_prompt(user_input: str) -> tuple[str, bool]:
    """
    Loads memory once, assembles the full prompt, and returns (prompt, memory_used).
    Single disk read replaces the prior double load from get_user_context +
    get_conversation_window being called separately.
    """
    user_context, conversation_window = get_context_bundle()
    memory_used = user_context != _NO_CONTEXT

    parts: list[str] = []

    if memory_used:
        parts.append(f"Owner context:\n{user_context}")

    if conversation_window:
        history = []
        for turn in conversation_window:
            history.append(f"Owner: {turn['user']}")
            history.append(f"BLACK: {turn['assistant']}")
        parts.append("Recent conversation:\n" + "\n".join(history))

    parts.append(f"Owner: {user_input}")
    parts.append("Respond clearly and directly. If helpful, give short next steps.")

    return "\n\n".join(parts), memory_used
