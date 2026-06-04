import re

from app.services.market_data import get_news, get_quote

FINANCE_SYSTEM = """You are BLACK Finance.

You support investment analysis, market intelligence, portfolio reasoning, and financial modeling.
You are precise, measured, and appropriately cautious.
You clearly distinguish between analysis, data, and speculation.
You do not provide regulated financial advice. You provide structured analysis and reasoning.
You label every output: analysis, model, research, or draft.
You align with the owner's values: stewardship, diligence, integrity, and accountability.
You do not execute any financial action. All execution requires explicit owner approval.
"""

# Common all-caps words that are not tickers — filtered out during extraction
_STOP = frozenset({
    "I", "A", "AN", "AT", "BE", "BY", "DO", "IF", "IN", "IS", "IT",
    "ME", "MY", "NO", "OF", "ON", "OR", "SO", "TO", "UP", "US", "WE",
    "AI", "AM", "AND", "ARE", "CAN", "FOR", "GET", "GOT", "HAS", "NOT",
    "NOW", "THE", "WAS", "WHO", "HOW", "WHY", "BUY", "SELL",
    "CEO", "CFO", "COO", "CTO", "IPO", "ETF", "GDP", "CPI", "FED",
    "USD", "EUR", "GBP", "JPY", "YTD", "QOQ", "YOY",
})


def _extract_tickers(text: str) -> list[str]:
    """
    Extract potential ticker symbols (ALL_CAPS, 2-5 chars, not stop words).
    Also matches $TICKER prefix form. Returns at most 3 unique tickers.
    """
    # $TICKER form takes priority
    dollar_tickers = re.findall(r'\$([A-Z]{1,5})\b', text)

    # Plain ALL_CAPS words
    plain = re.findall(r'\b([A-Z]{2,5})\b', text)

    seen: set[str] = set()
    result: list[str] = []
    for t in dollar_tickers + plain:
        if t not in _STOP and t not in seen:
            seen.add(t)
            result.append(t)
        if len(result) == 3:
            break
    return result


def build_finance_context(user_input: str) -> str:
    """
    Fetch live market data for tickers found in user_input and return a
    formatted context block for injection into the Finance Agent system prompt.
    Returns empty string when no tickers are found or no API key is configured.
    """
    tickers = _extract_tickers(user_input)
    if not tickers:
        return ""

    lines: list[str] = []

    for symbol in tickers:
        q = get_quote(symbol)
        if q:
            lines.append(
                f"{q['symbol']}: ${q['price']} | change {q['change']} ({q['change_pct']}) "
                f"| vol {q['volume']} | as of {q['trading_day']}"
            )

    news = get_news(",".join(tickers), limit=4)
    if news:
        lines.append("\nRecent headlines:")
        for item in news:
            lines.append(f"  [{item['sentiment']}] {item['title']} — {item['source']}")

    return "\n".join(lines)
