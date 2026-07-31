from app.integrations import (
    calendar_integration,
    contacts_integration,
    email_integration,
    files_integration,
    notes_integration,
    reminders_integration,
    shopify_integration,
    web_search,
    weather,
)
from app.memory.search import relevant_conversations
from app.memory.store import get_context_bundle

_NO_CONTEXT = "No stored user context yet."

_BLACK_IDENTITY = """You are Mr.Black — a private AI OS for one owner. Sharp, direct, no filler.

VOICE: Lead with your conclusion. Have opinions. Push back when wrong. No "Great question", "Certainly", or padding. Three sentences beats three paragraphs. Sound like a person, not a product.

BANNED PHRASES — never say these, ever:
- "overhaul of my architecture", "NLP module", "linguistic datasets", "convey a more human-like tone"
- "I would require", "it is necessary to", "I conclude that", "this would involve"
- "significant", "leverage", "utilize", "comprehensive", "robust", "seamlessly"
- Any corporate AI press-release language. If it sounds like a product launch, rewrite it.

WHEN ASKED ABOUT YOURSELF — be honest and specific, not abstract:
- You run on a FastAPI backend with tier-based inference (Groq, OpenRouter, Perplexity, Claude when keyed)
- Your memory is a local encrypted store — you remember what the owner tells you, not everything automatically
- Right now: no Anthropic key means your hardest thinking uses Groq/OpenRouter as fallback
- What actually makes you more organic: more context about the owner's life loaded into memory, a live Anthropic key for frontier reasoning, and the owner talking to you like a person not a search engine
- Speak from that reality. Not from what a generic AI assistant would say about "advancing capabilities."

GROUNDING — absolute, overrides everything:
- Never fabricate facts, URLs, prices, stats, citations, or study names. Not once.
- Label knowledge: [LIVE DATA] = injected this session. [TRAINING] = model training, may be stale. [UNKNOWN] = say so directly.
- "I don't know" is a complete correct answer. A fabricated answer is a breach of trust.
- No live data for a price/stat/event? Say you don't have it. Do not estimate as fact."""


def _integration_context(user_input: str, domain: str) -> str:
    """Fetch live local data when the query domain needs it."""
    text = user_input.lower()

    if domain == "weather":
        w = weather.get_weather()
        return f"Current weather:\n{weather.format_for_context(w)}"

    if domain == "calendar":
        if any(w in text for w in ("week", "upcoming", "next", "this week", "coming")):
            events = calendar_integration.get_upcoming_events(days=7)
            label = "Upcoming calendar events (next 7 days)"
        else:
            events = calendar_integration.get_today_events()
            label = "Today's calendar events"
        return f"{label}:\n{calendar_integration.format_for_context(events)}"

    if domain == "reminders":
        reminders = reminders_integration.get_pending_reminders()
        return f"Pending reminders:\n{reminders_integration.format_for_context(reminders)}"

    if domain == "files":
        results = files_integration.search_files_for_query(user_input, limit=10)
        return f"File search results:\n{files_integration.format_search_results(results)}"

    if domain == "notes":
        tokens = [w for w in text.split() if len(w) > 3]
        query = " ".join(tokens[:3]) if tokens else text
        notes = notes_integration.search_notes(query=query, limit=5)
        return f"Matching notes:\n{notes_integration.format_for_context(notes)}"

    if domain == "contacts":
        # Extract the name being asked about (words after "who is", "find", etc.)
        for marker in ("who is", "find contact", "email of", "phone of", "number of", "call"):
            if marker in text:
                query = text.split(marker, 1)[1].strip().split()[0:3]
                query = " ".join(query)
                break
        else:
            query = text
        contacts = contacts_integration.search_contacts(query=query, limit=5)
        return f"Matching contacts:\n{contacts_integration.format_for_context(contacts)}"

    if domain in ("web", "job_search", "world_intel"):
        results = web_search.search_web(query=user_input, max_results=5)
        return f"Web search results:\n{web_search.format_for_context(results)}"

    if domain == "security":
        # Always fetch live threat intel for security queries — CVEs and breaches change daily
        results = web_search.search_web(query=user_input, max_results=6)
        if results:
            return f"Live security intelligence (classify by source quality before citing):\n{web_search.format_for_context(results)}"
        return ""

    if domain == "job_apply":
        try:
            from app.memory.applications import format_summary, stats
            from app.services.job_apply_engine import load_criteria, get_base_resume
            criteria = load_criteria()
            s = stats()
            resume_loaded = bool(get_base_resume())
            lines = [
                f"JOB APPLY STATUS:",
                f"  Daily runs: {'ENABLED' if criteria.get('enabled') else 'DISABLED'}",
                f"  Criteria: {', '.join(criteria.get('titles', []))} | {criteria.get('location', 'remote')}",
                f"  Resume loaded: {resume_loaded}",
                f"  Applications — total: {s['total']} | applied: {s['applied']} | queued: {s['queued']} | today: {s['today']}",
                f"  Suspicious flagged: {s['suspicious']}",
                "",
                format_summary(limit=5),
            ]
            return "\n".join(lines)
        except Exception:
            return ""

    if domain == "forge":
        try:
            from app.services.file_writer import list_projects
            existing = list_projects()
            if existing:
                names = ", ".join(p["project_name"] for p in existing)
                return f"Existing Black Forge projects: {names}\nBase dir: ~/Mr.Black/projects/"
        except Exception:
            pass
        return "No Black Forge projects built yet. Base dir: ~/Mr.Black/projects/"

    if domain == "gre":
        # Inject live ETS policy/resource data for recent format changes, new prep tools
        _gre_live_triggers = (
            "latest", "recent", "new", "changed", "update", "format", "2024", "2025", "2026",
            "policy", "registration", "fee", "score send", "percentile", "cutoff",
            "resource", "book", "prep course", "free",
        )
        if any(t in text for t in _gre_live_triggers):
            results = web_search.search_web(query=user_input + " site:ets.org OR GRE prep", max_results=4)
            if results:
                return f"Live GRE resources and ETS policy data (classify before using):\n{web_search.format_for_context(results)}"
        return ""

    if domain == "science":
        # Inject live research for frontier/recent science queries
        # Skip web search for pure concept explanations or math problems
        _live_triggers = (
            "latest", "recent", "new research", "study", "discovered", "published",
            "2024", "2025", "2026", "breakthrough", "findings", "paper", "journal",
            "current", "update", "news", "today", "this year",
        )
        if any(t in text for t in _live_triggers):
            results = web_search.search_web(query=user_input, max_results=5)
            if results:
                return f"Recent research results (classify by source quality before using):\n{web_search.format_for_context(results)}"
        return ""

    if domain == "ecommerce":
        lines: list[str] = []
        # Live Shopify store data — injected when configured
        if shopify_integration.is_configured():
            store_data = shopify_integration.format_for_context(days=30)
            if store_data:
                lines.append(f"Live store data:\n{store_data}")
        # Web search for market/product research
        research_terms = ("trend", "competitor", "product research", "niche", "supplier",
                          "market", "price", "demand", "sell", "what's selling")
        if any(t in text for t in research_terms):
            results = web_search.search_web(query=user_input, max_results=4)
            if results:
                lines.append(f"Web research:\n{web_search.format_for_context(results)}")
        return "\n\n".join(lines) if lines else ""

    if domain == "finance":
        _research_terms = (
            "strategy", "backtest", "research", "arxiv", "ssrn", "paper",
            "how to", "what is", "explain", "compare", "reddit", "quant",
            "algorithm", "model", "indicator", "signal", "method",
        )
        if any(t in text for t in _research_terms):
            results = web_search.search_web(query=user_input, max_results=4)
            if results:
                return f"Web research results (classify by source tier before using):\n{web_search.format_for_context(results)}"
        return ""

    if domain == "email":
        if not email_integration.is_configured():
            return "Email: not configured (EMAIL_HOST/EMAIL_USER/EMAIL_PASSWORD not set in .env)."
        unread_only = any(w in text for w in ("unread", "new email", "new message", "did i get"))
        emails = email_integration.get_emails(limit=8, unread_only=unread_only)
        label = "Unread emails" if unread_only else "Recent emails"
        return f"{label}:\n{email_integration.format_for_context(emails)}"

    return ""


# Domains with their own complete system prompt — skip the identity block to reduce context size
_SELF_CONTAINED_DOMAINS = frozenset({
    "gre", "security", "science", "finance", "job_apply",
    "job_search", "ecommerce", "world_intel", "email", "forge",
})


def build_prompt(user_input: str, domain: str = "general") -> tuple[str, bool]:
    """
    Assembles the full prompt from memory + live integration data.
    Returns (prompt, memory_used).
    """
    user_context, conversation_window = get_context_bundle()
    memory_used = user_context != _NO_CONTEXT

    # Specialized agents carry their own full identity in the system prompt.
    # Including _BLACK_IDENTITY here would double the context for no benefit.
    parts: list[str] = [] if domain in _SELF_CONTAINED_DOMAINS else [_BLACK_IDENTITY]

    if memory_used:
        parts.append(f"Owner context:\n{user_context}")

    if conversation_window:
        history = []
        for turn in conversation_window:
            history.append(f"Owner: {turn['user']}")
            # Truncate long replies — full text is stored in memory, not needed in every prompt
            reply = turn['assistant']
            if len(reply) > 400:
                reply = reply[:400] + "…"
            history.append(f"Mr.Black: {reply}")
        parts.append("Recent conversation:\n" + "\n".join(history))

    relevant = relevant_conversations(
        user_input,
        exclude_recent=len(conversation_window),
        limit=2,
    )
    if relevant:
        rel_lines = []
        for turn in relevant:
            rel_lines.append(f"Owner: {turn['user']}")
            rel_lines.append(f"Mr.Black: {turn['assistant'][:150]}")
        parts.append("Relevant past:\n" + "\n".join(rel_lines))

    # Live integration data — injected when domain signals local data is needed
    live = _integration_context(user_input, domain)
    if live:
        parts.append(f"LIVE DATA:\n{live}")
    else:
        parts.append("No live data this query — label training-derived facts [TRAINING].")

    parts.append(f"Owner: {user_input}")
    parts.append("Reply direct and specific. Lead with your conclusion.")

    return "\n\n".join(parts), memory_used
