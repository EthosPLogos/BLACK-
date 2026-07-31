"""
Auto-summarizer: when conversations reach 80% of MAX_CONVERSATIONS,
compress the oldest batch into durable facts using the LLM.
Called from add_conversation() — runs at most once per ~80 conversations.
"""
import re
from datetime import datetime, timezone

from app.config import MAX_CONVERSATIONS, MAX_FACTS

_THRESHOLD = 0.8
_BATCH_SIZE = 20
_MAX_FACTS_PER_BATCH = 8

_SYSTEM = (
    "You extract concise, durable facts from conversation history. "
    "Each fact must be one sentence, highly specific, and worth remembering long-term. "
    "Focus on decisions made, preferences revealed, projects discussed, and key outcomes. "
    "Return only a numbered list of facts. No headers, no explanations."
)


def _parse_facts(text: str) -> list[str]:
    facts = []
    for line in text.splitlines():
        line = line.strip()
        line = re.sub(r'^[\d\.\-\*•]+\s*', '', line)
        if line and len(line) > 15:
            facts.append(line)
    return facts[:_MAX_FACTS_PER_BATCH]


def maybe_summarize(memory: dict) -> dict:
    """
    Check if memory needs summarization and run it if so.
    Modifies and returns the memory dict (caller must save).
    Returns memory unchanged if threshold not reached or inference fails.
    """
    from app.services.inference import call_inference

    convs = memory.get("conversations", [])
    if len(convs) < MAX_CONVERSATIONS * _THRESHOLD:
        return memory

    batch = convs[:_BATCH_SIZE]
    remaining = convs[_BATCH_SIZE:]

    formatted = "\n\n".join(
        f"Owner: {c.get('user', '')}\nBLACK: {c.get('assistant', '')[:300]}"
        for c in batch
    )
    prompt = (
        f"Extract the most important facts from these {len(batch)} conversations "
        f"that should be remembered permanently:\n\n{formatted}"
    )

    try:
        reply, _ = call_inference(prompt, _SYSTEM)
        facts = _parse_facts(reply)
        if not facts:
            return memory

        memory["conversations"] = remaining
        now = datetime.now(timezone.utc).isoformat()
        for fact in facts:
            memory.setdefault("memories", []).append({
                "fact": fact,
                "timestamp": now,
                "source": "auto_summarize",
            })

        if len(memory["memories"]) > MAX_FACTS:
            memory["memories"] = memory["memories"][-MAX_FACTS:]

    except Exception:
        pass

    return memory
