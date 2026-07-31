"""
Typed state object for a finance research pipeline run.
Passed between research steps; LLM synthesis only happens once at the end.

Adapted from the financial-research-agent spec.
LangGraph-compatible (TypedDict) but runs natively in Mr. Black without LangGraph.
If LangGraph is added later, this drops in unchanged.
"""
from typing import Any, Optional
from typing import TypedDict


class ResearchState(TypedDict, total=False):
    # Input
    ticker: str
    user_query: Optional[str]

    # Data collected by each research step (LLM-free)
    quote_data: Optional[dict[str, Any]]
    price_history: Optional[dict[str, Any]]
    news_sentiment: Optional[list[dict[str, Any]]]

    # Reasoning trace — one entry per step, written before LLM call
    reasoning_steps: list[str]

    # LLM synthesis output
    signal: Optional[str]        # "bullish" | "bearish" | "neutral"
    confidence: Optional[float]  # 0.0 – 1.0
    summary: Optional[str]

    # Error state — set by any step on failure; pipeline short-circuits
    error: Optional[str]
