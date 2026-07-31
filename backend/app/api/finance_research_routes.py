"""
Structured finance research endpoint.

POST /api/finance/research  →  { signal, confidence, summary, reasoning_steps }

Pipeline (data-first, LLM-last — only one LLM call per research run):
  1. fetch_quote    — Alpaca real-time snapshot
  2. fetch_history  — Alpaca 90-day daily bars
  3. fetch_news     — Alpha Vantage news + sentiment
  4. synthesize     — LLM reads all data, returns signal + summary

No trade execution here. Read-only. Paper-safe.
"""
import json

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agent.state import ResearchState
from app.audit import logger as audit
from app.integrations.alpaca_integration import get_price_history, get_snapshot
from app.services.inference import call_inference
from app.services.market_data import get_news

router = APIRouter(prefix="/api/finance", tags=["Finance Research"])


class ResearchRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    days: int = Field(default=90, ge=7, le=365)


class ResearchResponse(BaseModel):
    ticker: str
    signal: str
    confidence: float
    summary: str
    reasoning_steps: list[str]
    error: str | None = None


_SYNTHESIZE_SYSTEM = """You are Mr. Black's Finance Research Agent.

You receive structured market data and produce a concise research signal.
You do NOT give investment advice. You produce a structured research summary only.

Rules:
- Base your signal ONLY on the data provided. Never invent facts.
- If data is missing or thin, lower your confidence accordingly.
- Confidence 0.0 = complete uncertainty. 1.0 = very strong signal from data.
- Keep the summary to 3-4 plain sentences. Cite the data.
- signal must be exactly one of: bullish, bearish, neutral

Return ONLY valid JSON:
{
  "signal": "bullish" | "bearish" | "neutral",
  "confidence": 0.0-1.0,
  "summary": "..."
}"""


def _run_research_pipeline(ticker: str, days: int = 90) -> ResearchState:
    """
    Execute the research pipeline. Data steps are deterministic; LLM is called once at the end.
    """
    state: ResearchState = {
        "ticker": ticker.upper(),
        "reasoning_steps": [],
        "signal": "neutral",
        "confidence": 0.0,
        "summary": "",
        "error": None,
    }

    # Step 1: Latest quote
    try:
        quote = get_snapshot(ticker)
        state["quote_data"] = quote
        if quote:
            state["reasoning_steps"].append(
                f"Quote: {ticker} @ ${quote.get('price')} "
                f"({quote.get('change_pct', 0):+.2f}% today, "
                f"vol {quote.get('volume', 'N/A')})"
            )
        else:
            state["reasoning_steps"].append(f"Quote: Alpaca not configured or {ticker} not found")
    except Exception as exc:
        state["reasoning_steps"].append(f"Quote fetch failed: {exc}")

    if state.get("error"):
        return state

    # Step 2: Price history
    try:
        history = get_price_history(ticker, days=days)
        state["price_history"] = history
        if history:
            state["reasoning_steps"].append(
                f"History ({days}d): open ${history.get('open_price')}, "
                f"latest ${history.get('latest_close')}, "
                f"return {history.get('period_return_pct', 0):+.2f}%, "
                f"high ${history.get('period_high')}, low ${history.get('period_low')}"
            )
        else:
            state["reasoning_steps"].append(f"History: unavailable for {ticker}")
    except Exception as exc:
        state["reasoning_steps"].append(f"History fetch failed: {exc}")

    # Step 3: News sentiment
    try:
        news = get_news(ticker, limit=5)
        state["news_sentiment"] = news
        if news:
            sentiments = [n.get("sentiment", "Neutral") for n in news]
            state["reasoning_steps"].append(
                f"News ({len(news)} articles): {', '.join(sentiments[:5])}"
            )
        else:
            state["reasoning_steps"].append("News: unavailable (Alpha Vantage key not set or rate-limited)")
    except Exception as exc:
        state["reasoning_steps"].append(f"News fetch failed: {exc}")

    # Step 4: LLM synthesis — only LLM call in the pipeline
    data_block = json.dumps({
        "ticker": ticker,
        "quote": state.get("quote_data"),
        "price_history": state.get("price_history"),
        "news_headlines": [
            {"title": n.get("title"), "sentiment": n.get("sentiment")}
            for n in (state.get("news_sentiment") or [])
        ],
    }, default=str)

    prompt = (
        f"Research data for {ticker}:\n\n{data_block}\n\n"
        "Analyze and return the JSON signal object."
    )

    try:
        raw, _ = call_inference(prompt=prompt, system=_SYNTHESIZE_SYSTEM, tier="frontier")
        import re
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)
        state["signal"] = parsed.get("signal", "neutral")
        state["confidence"] = float(parsed.get("confidence", 0.0))
        state["summary"] = parsed.get("summary", "")
        state["reasoning_steps"].append("LLM synthesis complete")
    except Exception as exc:
        state["error"] = f"Synthesis failed: {exc}"
        state["reasoning_steps"].append(f"LLM synthesis error: {exc}")

    return state


@router.post("/research", response_model=ResearchResponse)
def research(request: ResearchRequest):
    ticker = request.ticker.upper()
    audit.log_event("finance_research_requested", {"ticker": ticker, "days": request.days})

    state = _run_research_pipeline(ticker, days=request.days)

    audit.log_event(
        "finance_research_complete",
        {
            "ticker": ticker,
            "signal": state.get("signal"),
            "confidence": state.get("confidence"),
            "steps": len(state.get("reasoning_steps", [])),
            "error": state.get("error"),
        },
    )

    return ResearchResponse(
        ticker=ticker,
        signal=state.get("signal", "neutral"),
        confidence=state.get("confidence", 0.0),
        summary=state.get("summary", ""),
        reasoning_steps=state.get("reasoning_steps", []),
        error=state.get("error"),
    )
