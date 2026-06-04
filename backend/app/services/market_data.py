"""
Alpha Vantage read-only market data client.

Free tier: 25 requests/day, 5/minute.
Results are cached per-symbol for 5 minutes to conserve the daily quota.

ALPHA_VANTAGE_API_KEY must be set in backend/.env to enable data injection.
When empty, all functions return None/[] and the Finance Agent reasons from
LLM training knowledge only.
"""
import time

import httpx

from app.config import ALPHA_VANTAGE_API_KEY

_BASE = "https://www.alphavantage.co/query"
_CACHE_TTL = 300  # 5 minutes

_quote_cache: dict[str, tuple[float, dict]] = {}
_news_cache: dict[str, tuple[float, list]] = {}


def _stale(ts: float) -> bool:
    return time.time() - ts > _CACHE_TTL


def get_quote(symbol: str) -> dict | None:
    """
    Fetch current price quote for a ticker symbol.
    Returns dict with price/change/volume keys, or None if unavailable.
    """
    if not ALPHA_VANTAGE_API_KEY:
        return None

    if symbol in _quote_cache:
        ts, data = _quote_cache[symbol]
        if not _stale(ts):
            return data

    try:
        r = httpx.get(
            _BASE,
            params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": ALPHA_VANTAGE_API_KEY},
            timeout=5.0,
        )
        q = r.json().get("Global Quote", {})
        if not q or "05. price" not in q:
            return None  # unknown symbol or rate-limited
        result = {
            "symbol": q.get("01. symbol", symbol),
            "price": q.get("05. price"),
            "change": q.get("09. change"),
            "change_pct": q.get("10. change percent"),
            "volume": q.get("06. volume"),
            "trading_day": q.get("07. latest trading day"),
        }
        _quote_cache[symbol] = (time.time(), result)
        return result
    except Exception:
        return None


def get_news(tickers: str, limit: int = 5) -> list[dict]:
    """
    Fetch recent news headlines and sentiment for a comma-separated ticker list.
    Returns up to `limit` articles, or [] if unavailable.
    """
    if not ALPHA_VANTAGE_API_KEY:
        return []

    if tickers in _news_cache:
        ts, data = _news_cache[tickers]
        if not _stale(ts):
            return data

    try:
        r = httpx.get(
            _BASE,
            params={"function": "NEWS_SENTIMENT", "tickers": tickers,
                    "limit": limit, "apikey": ALPHA_VANTAGE_API_KEY},
            timeout=8.0,
        )
        articles = r.json().get("feed", [])[:limit]
        result = [
            {
                "title": a.get("title", ""),
                "source": a.get("source", ""),
                "published": a.get("time_published", ""),
                "summary": a.get("summary", "")[:200],
                "sentiment": a.get("overall_sentiment_label", "Neutral"),
            }
            for a in articles
        ]
        _news_cache[tickers] = (time.time(), result)
        return result
    except Exception:
        return []
