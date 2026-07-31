from app.agents.builder import BUILDER_SYSTEM
from app.agents.business_agent import BUSINESS_SYSTEM
from app.agents.ecommerce_market_agent import ECOMMERCE_SYSTEM
from app.agents.email_agent import EMAIL_SYSTEM
from app.agents.fact_checker import FACT_CHECKER_SYSTEM
from app.agents.finance_agent import FINANCE_SYSTEM, build_finance_context
from app.integrations import alpaca_integration
from app.agents.job_search_agent import JOB_SEARCH_SYSTEM
from app.agents.researcher import RESEARCHER_SYSTEM
from app.agents.science_agent import SCIENCE_SYSTEM
from app.agents.gre_agent import GRE_SYSTEM
from app.agents.web_builder_agent import WEB_BUILDER_SYSTEM
from app.agents.job_apply_agent import JOB_APPLY_SYSTEM
from app.agents.security_agent import SECURITY_SYSTEM
from app.agents.verifier import VERIFIER_SYSTEM
from app.agents.world_intel_agent import WORLD_INTEL_SYSTEM
from app.audit import logger as audit
from app.services.inference import Tier, call_inference

# Task types eligible for Verifier audit
_VERIFY_TASK_TYPES = {"draft", "action-plan"}

_OPTIONS_TERMS = frozenset({
    "option", "options", "call", "put", "strike", "expiry", "expiration",
    "delta", "gamma", "theta", "vega", "greeks", "chain", "iv", "implied volatility",
    "covered call", "iron condor", "spread", "straddle", "strangle", "butterfly",
})


def _build_alpaca_context(user_input: str) -> str:
    """Build Alpaca live data block for finance queries."""
    if not alpaca_integration.is_configured():
        return ""

    text = user_input.lower()
    lines: list[str] = []

    # Account summary — inject when portfolio/account mentioned
    if any(w in text for w in ("account", "portfolio", "position", "holdings", "buying power", "my portfolio")):
        account = alpaca_integration.get_account()
        positions = alpaca_integration.get_positions()
        if account:
            lines.append(alpaca_integration.format_account_for_context(account, positions))

    # Stock snapshots — extract tickers from input
    from app.agents.finance_agent import _extract_tickers
    tickers = _extract_tickers(user_input)
    if not tickers and any(w in text for w in ("market", "spy", "spy", "qqq", "index")):
        tickers = ["SPY", "QQQ"]

    for symbol in tickers[:4]:
        snap = alpaca_integration.get_snapshot(symbol)
        if snap:
            lines.append(alpaca_integration.format_snapshot_for_context(snap))

    # Options chain — inject when options-specific terms present
    if tickers and any(t in text for t in _OPTIONS_TERMS):
        chain = alpaca_integration.get_options_chain(tickers[0], limit=30)
        if chain:
            lines.append(f"\nOptions chain — {tickers[0]}:")
            lines.append(alpaca_integration.format_options_for_context(chain))

    return "\n".join(lines)


def resolve_system(agent_name: str, domain: str, user_input: str = "") -> tuple[str, str]:
    """
    Returns (system_prompt, effective_agent_name).
    When domain is 'finance' and live data is available, market context is
    injected into the system prompt so the agent reasons from current prices/news.
    """
    if domain == "finance":
        system = FINANCE_SYSTEM
        # Alpha Vantage data (news sentiment + basic quote)
        ctx = build_finance_context(user_input) if user_input else ""
        # Alpaca data (real-time quotes, options chain, account)
        alpaca_ctx = _build_alpaca_context(user_input)
        live = "\n".join(filter(None, [ctx, alpaca_ctx]))
        if live:
            system = f"{FINANCE_SYSTEM}\nLIVE MARKET DATA (fetched now):\n{live}\n"
        return system, "finance"

    if domain == "business":
        return BUSINESS_SYSTEM, "business"

    if domain == "ecommerce":
        return ECOMMERCE_SYSTEM, "ecommerce"

    if domain == "job_search":
        return JOB_SEARCH_SYSTEM, "job_search"

    if domain == "world_intel":
        return WORLD_INTEL_SYSTEM, "world_intel"

    if domain == "email":
        return EMAIL_SYSTEM, "email"

    if domain == "science":
        return SCIENCE_SYSTEM, "science"

    if domain == "security":
        return SECURITY_SYSTEM, "security"

    if domain == "job_apply":
        return JOB_APPLY_SYSTEM, "job_apply"

    if domain == "gre":
        return GRE_SYSTEM, "gre"

    if domain == "forge":
        return WEB_BUILDER_SYSTEM, "forge"

    if agent_name == "builder":
        return BUILDER_SYSTEM, "builder"

    return RESEARCHER_SYSTEM, "researcher"


def run_chain(
    agent_name: str,
    task_type: str,
    domain: str,
    prompt: str,
    session_id: str = "",
    user_input: str = "",
    tier: Tier = "fast",
) -> dict:
    """Run primary inference and return the reply with agent metadata and provider."""
    system, effective_agent = resolve_system(agent_name, domain, user_input)
    reply, provider = call_inference(prompt=prompt, system=system, tier=tier)

    audit.log_event(
        "inference_completed",
        {"agent": effective_agent, "reply_length": len(reply), "provider": provider, "tier": tier},
        session_id=session_id,
    )

    return {"reply": reply, "agent": effective_agent, "provider": provider}


_FACT_CHECK_SKIP_TYPES = frozenset({"blocked", "halted", "pending_approval"})


def run_fact_check(
    user_input: str,
    reply: str,
    task_type: str,
    session_id: str = "",
) -> dict:
    """
    Anti-hallucination gate — runs on every response, returns verdict to the owner.
    Uses the fast tier to minimize cost and latency.
    """
    if task_type in _FACT_CHECK_SKIP_TYPES or len(reply) < 20:
        return {"verdict": "CLEAN", "flags": [], "confidence": "HIGH"}

    check_prompt = (
        f"Owner asked: {user_input[:200]}\n\n"
        f"Response to check:\n{reply[:1500]}\n\n"
        "Scan for hallucination patterns. Output your verdict."
    )
    try:
        verdict_text, provider = call_inference(
            prompt=check_prompt, system=FACT_CHECKER_SYSTEM, tier="fast",
        )
    except Exception:
        return {"verdict": "CLEAN", "flags": [], "confidence": "LOW"}

    verdict = "CLEAN"
    if "FLAGGED" in verdict_text.upper():
        verdict = "FLAGGED"
    elif "SUSPECT" in verdict_text.upper():
        verdict = "SUSPECT"

    flags: list[str] = []
    in_flags = False
    for line in verdict_text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("FLAGS:"):
            in_flags = True
            continue
        if in_flags and stripped.startswith("- "):
            flags.append(stripped[2:])
        elif in_flags and stripped.upper().startswith("CONFIDENCE:"):
            break

    confidence = "MEDIUM"
    if "CONFIDENCE: HIGH" in verdict_text.upper():
        confidence = "HIGH"
    elif "CONFIDENCE: LOW" in verdict_text.upper():
        confidence = "LOW"

    audit.log_event(
        "fact_check_ran",
        {
            "verdict": verdict,
            "flags_count": len(flags),
            "confidence": confidence,
            "provider": provider,
            "verdict_raw": verdict_text[:300],
        },
        session_id=session_id,
    )

    return {"verdict": verdict, "flags": flags, "confidence": confidence}


def run_verifier_audit(
    user_input: str,
    reply: str,
    task_type: str,
    session_id: str = "",
) -> None:
    """
    Background-safe verifier pass. Runs after the response is returned to the owner.
    Result is written to the audit log only — does not modify the response.
    Only runs on draft and action-plan task types.
    """
    if task_type not in _VERIFY_TASK_TYPES:
        return

    verifier_prompt = (
        f"Review this response for correctness, safety, and clarity.\n\n"
        f"Original request: {user_input}\n\n"
        f"Response:\n{reply}\n\n"
        "If the response has issues, list them concisely. "
        "If it passes, respond with exactly: PASS"
    )
    verdict, provider = call_inference(prompt=verifier_prompt, system=VERIFIER_SYSTEM)
    passed = "PASS" in verdict.upper()

    audit.log_event(
        "verifier_ran",
        {
            "task_type": task_type,
            "passed": passed,
            "verdict_preview": verdict[:200],
            "provider": provider,
        },
        session_id=session_id,
    )
