from datetime import datetime

from fastapi import APIRouter

from app.agents.researcher import RESEARCHER_SYSTEM
from app.integrations import (
    calendar_integration,
    reminders_integration,
    web_search,
    weather,
)
from app.services.inference import call_inference

router = APIRouter(prefix="/api/brief", tags=["brief"])


@router.get("")
def daily_brief():
    """Return weather, calendar, reminders, and news — data only, no LLM."""
    now = datetime.now()
    try:
        weather_data = weather.get_weather()
    except Exception:
        weather_data = {}
    try:
        events = calendar_integration.get_today_events()
    except Exception:
        events = []
    try:
        reminders = reminders_integration.get_pending_reminders()
    except Exception:
        reminders = []
    try:
        news = web_search.search_web("today's top news headlines", max_results=4)
    except Exception:
        news = []
    return {
        "date": now.strftime("%A, %B %d, %Y"),
        "time": now.strftime("%I:%M %p"),
        "weather": weather_data,
        "events": events,
        "reminders": reminders,
        "news": news,
    }


@router.post("/summary")
def brief_summary(body: dict):
    """Generate an LLM morning summary from the provided brief data."""
    now = datetime.now()
    weather_data = body.get("weather", {})
    events = body.get("events", [])
    reminders = body.get("reminders", [])
    news = body.get("news", [])

    weather_str = weather.format_for_context(weather_data)
    events_str = calendar_integration.format_for_context(events)
    reminders_str = reminders_integration.format_for_context(reminders)
    news_lines = "\n".join(f"- {r['title']}: {r['snippet'][:120]}" for r in news) or "No headlines."

    prompt = (
        f"Today is {now.strftime('%A, %B %d, %Y')} at {now.strftime('%I:%M %p')}.\n\n"
        f"Weather: {weather_str}\n\n"
        f"Calendar today:\n{events_str}\n\n"
        f"Pending reminders:\n{reminders_str}\n\n"
        f"Top news:\n{news_lines}\n\n"
        "Write a concise 3-4 sentence morning summary. Mention weather, "
        "highlight key events or reminders, note relevant news. Be warm and practical."
    )
    try:
        summary, _ = call_inference(prompt=prompt, system=RESEARCHER_SYSTEM)
    except Exception:
        summary = "Summary unavailable — Ollama may be offline."

    return {"summary": summary}
