"""
Keyword-scored memory search across facts and conversations.
No external model required — uses TF * coverage scoring.
Returns results sorted by relevance descending.
"""
import re

from app.memory.store import load_memory

_STOP = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
    "i", "my", "me", "we", "you", "it", "this", "that", "what", "how",
    "do", "did", "can", "will", "would", "should", "about", "just", "if",
    "not", "no", "so", "as", "up", "out", "than", "then", "when", "has",
})


def _tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r'\b[a-z0-9]+\b', text.lower()) if w not in _STOP and len(w) > 1]


def _score(query_terms: set[str], doc_terms: list[str]) -> float:
    if not query_terms or not doc_terms:
        return 0.0
    doc_set = set(doc_terms)
    matches = query_terms & doc_set
    if not matches:
        return 0.0
    tf = sum(doc_terms.count(t) for t in matches)
    coverage = len(matches) / len(query_terms)
    return round(tf * coverage, 4)


def search_memory(query: str, limit: int = 5) -> list[dict]:
    """
    Search facts and conversations by keyword relevance.
    Returns up to `limit` results sorted by score descending.
    """
    memory = load_memory()
    query_terms = set(_tokenize(query))
    if not query_terms:
        return []

    results: list[dict] = []

    for item in memory.get("memories", []):
        fact = item.get("fact", "")
        score = _score(query_terms, _tokenize(fact))
        if score > 0:
            results.append({
                "type": "fact",
                "content": fact,
                "score": score,
                "timestamp": item.get("timestamp"),
            })

    for conv in memory.get("conversations", []):
        text = f"{conv.get('user', '')} {conv.get('assistant', '')}"
        score = _score(query_terms, _tokenize(text))
        if score > 0:
            results.append({
                "type": "conversation",
                "user": conv.get("user", "")[:200],
                "assistant": conv.get("assistant", "")[:200],
                "score": score,
                "timestamp": conv.get("timestamp"),
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def relevant_conversations(query: str, exclude_recent: int = 3, limit: int = 3) -> list[dict]:
    """
    Return up to `limit` conversations relevant to `query`, skipping the
    most recent `exclude_recent` (those are injected via the normal window).
    Used by the context builder to enrich prompts with older but relevant memory.
    """
    memory = load_memory()
    convs = memory.get("conversations", [])
    query_terms = set(_tokenize(query))
    if not query_terms or len(convs) <= exclude_recent:
        return []

    candidates = convs[:-exclude_recent] if exclude_recent else convs
    scored = []
    for conv in candidates:
        text = f"{conv.get('user', '')} {conv.get('assistant', '')}"
        score = _score(query_terms, _tokenize(text))
        if score > 0:
            scored.append((score, conv))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:limit]]
