import httpx

from app.config import WEATHER_LOCATION


def get_weather(location: str = "") -> dict:
    """Fetch current weather and today's forecast from wttr.in (no API key needed)."""
    loc = (location or WEATHER_LOCATION).strip().replace(" ", "+")
    url = f"https://wttr.in/{loc}?format=j1"
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(url, follow_redirects=True)
            r.raise_for_status()
            data = r.json()

        current = data["current_condition"][0]
        today = data["weather"][0]
        area_list = data.get("nearest_area", [{}])
        area = area_list[0] if area_list else {}
        city = (area.get("areaName") or [{}])[0].get("value", "")
        country = (area.get("country") or [{}])[0].get("value", "")

        return {
            "temp_f": current["temp_F"],
            "temp_c": current["temp_C"],
            "feels_like_f": current["FeelsLikeF"],
            "description": current["weatherDesc"][0]["value"],
            "humidity": current["humidity"],
            "wind_mph": current["windspeedMiles"],
            "high_f": today["maxtempF"],
            "low_f": today["mintempF"],
            "city": city,
            "country": country,
        }
    except Exception:
        return {}


def format_for_context(weather: dict) -> str:
    if not weather:
        return "Weather unavailable."
    loc = f"{weather['city']}, {weather['country']} — " if weather.get("city") else ""
    return (
        f"{loc}{weather.get('description', 'Unknown')} · "
        f"{weather.get('temp_f', '?')}°F "
        f"(feels like {weather.get('feels_like_f', '?')}°F) · "
        f"High {weather.get('high_f', '?')}°F / Low {weather.get('low_f', '?')}°F · "
        f"Humidity {weather.get('humidity', '?')}% · "
        f"Wind {weather.get('wind_mph', '?')} mph"
    )
