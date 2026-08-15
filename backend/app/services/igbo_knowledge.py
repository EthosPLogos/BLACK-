"""
Igbo vocabulary knowledge base — search and context injection.

Loads igbo_vocabulary.json (extracted from We Speak Igbo seed.ts) once at startup.
At query time, searches for relevant items and injects them as structured context
for the Igbo Language Agent — same pattern as Finance + Alpaca live data.
"""
import json
import re
from pathlib import Path
from functools import lru_cache

_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "igbo_vocabulary.json"

_MAX_INJECT_ITEMS = 20  # cap context window usage


@lru_cache(maxsize=1)
def _load() -> dict:
    if not _DATA_PATH.exists():
        return {"lessons": [], "total_items": 0}
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _all_items() -> list[dict]:
    data = _load()
    items = []
    for lesson in data.get("lessons", []):
        for item in lesson.get("items", []):
            items.append({**item, "_lesson_id": lesson["id"], "_lesson_title": lesson["title"]})
    return items


def _score(item: dict, tokens: set[str]) -> int:
    score = 0
    igbo_lower = item.get("igbo", "").lower()
    english_lower = item.get("english", "").lower()
    tags = {t.lower() for t in item.get("tags", [])}
    lesson_title = item.get("_lesson_title", "").lower()

    for tok in tokens:
        if tok in igbo_lower:
            score += 3
        if tok in english_lower:
            score += 2
        if tok in tags:
            score += 2
        if tok in lesson_title:
            score += 1
    return score


def search(query: str, limit: int = _MAX_INJECT_ITEMS) -> list[dict]:
    """Return vocab items most relevant to the query, scored by keyword overlap."""
    tokens = {t.lower() for t in re.split(r'\W+', query) if len(t) > 2}
    if not tokens:
        return []

    items = _all_items()
    scored = [(item, _score(item, tokens)) for item in items]
    scored = [(item, s) for item, s in scored if s > 0]
    scored.sort(key=lambda x: -x[1])
    return [item for item, _ in scored[:limit]]


def get_lesson(lesson_id: str) -> dict | None:
    """Return a full lesson by ID."""
    for lesson in _load().get("lessons", []):
        if lesson["id"] == lesson_id:
            return lesson
    return None


def get_all_lessons_summary() -> list[dict]:
    """Compact lesson list for agent awareness."""
    return [
        {
            "id": l["id"],
            "title": l["title"],
            "igboTitle": l["igboTitle"],
            "level": l["level"],
            "item_count": len(l.get("items", [])),
        }
        for l in _load().get("lessons", [])
    ]


def build_context(query: str) -> str:
    """
    Build the vocabulary context block injected into the Igbo agent's system prompt.
    Returns empty string if no relevant items found.
    """
    # Check if asking for a specific lesson
    lessons_summary = get_all_lessons_summary()
    lesson_ids = {l["id"] for l in lessons_summary}
    query_lower = query.lower()

    # Direct lesson request (e.g. "teach me greetings", "show me numbers")
    matched_lesson = None
    for ls in lessons_summary:
        if ls["id"] in query_lower or ls["title"].lower() in query_lower:
            matched_lesson = get_lesson(ls["id"])
            break

    if matched_lesson:
        items = matched_lesson.get("items", [])
        block = (
            f"IGBO VOCABULARY CONTEXT — Lesson: {matched_lesson['title']} "
            f"({matched_lesson['igboTitle']}) [{matched_lesson['level']}]\n"
        )
        if matched_lesson.get("grammar"):
            block += f"Grammar note: {matched_lesson['grammar']}\n"
        block += f"Items ({len(items)}):\n"
        for item in items:
            line = f"  {item.get('igbo')} → {item.get('english')} ({item.get('part_of_speech', '')})"
            if item.get("example_sentence"):
                line += f" | e.g. \"{item['example_sentence']}\""
            if item.get("cultural_note"):
                line += f" | {item['cultural_note']}"
            if item.get("tone_note"):
                line += f" | TONE: {item['tone_note']}"
            block += line + "\n"
        return block

    # Keyword search for everything else
    results = search(query)
    if not results:
        # Inject lessons summary so agent knows what topics are available
        block = "IGBO VOCABULARY CONTEXT — Available lessons:\n"
        for ls in lessons_summary:
            block += f"  [{ls['level']}] {ls['title']} ({ls['igboTitle']}) — {ls['item_count']} items\n"
        return block

    block = f"IGBO VOCABULARY CONTEXT — {len(results)} relevant items:\n"
    for item in results:
        line = f"  {item.get('igbo')} → {item.get('english')} ({item.get('part_of_speech', '')})"
        if item.get("example_sentence"):
            line += f" | e.g. \"{item['example_sentence']}\""
        if item.get("cultural_note"):
            line += f" | {item['cultural_note']}"
        if item.get("tone_note"):
            line += f" | TONE: {item['tone_note']}"
        block += line + "\n"
    return block
