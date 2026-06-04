from app.agents.builder import BUILDER_SYSTEM
from app.agents.business_agent import BUSINESS_SYSTEM
from app.agents.finance_agent import FINANCE_SYSTEM, build_finance_context
from app.agents.researcher import RESEARCHER_SYSTEM
from app.agents.verifier import VERIFIER_SYSTEM
from app.audit import logger as audit
from app.services.inference import call_inference

# Task types eligible for Verifier audit
_VERIFY_TASK_TYPES = {"draft", "action-plan"}


def resolve_system(agent_name: str, domain: str, user_input: str = "") -> tuple[str, str]:
    """
    Returns (system_prompt, effective_agent_name).
    When domain is 'finance' and live data is available, market context is
    injected into the system prompt so the agent reasons from current prices/news.
    """
    if domain == "finance":
        system = FINANCE_SYSTEM
        ctx = build_finance_context(user_input) if user_input else ""
        if ctx:
            system = f"{FINANCE_SYSTEM}\nLIVE MARKET DATA (fetched now):\n{ctx}\n"
        return system, "finance"

    if domain == "business":
        return BUSINESS_SYSTEM, "business"

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
) -> dict:
    """Run primary inference and return the reply with agent metadata and provider."""
    system, effective_agent = resolve_system(agent_name, domain, user_input)
    reply, provider = call_inference(prompt=prompt, system=system)

    audit.log_event(
        "inference_completed",
        {"agent": effective_agent, "reply_length": len(reply), "provider": provider},
        session_id=session_id,
    )

    return {"reply": reply, "agent": effective_agent, "provider": provider}


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
