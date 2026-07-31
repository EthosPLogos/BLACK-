"""
BLACK-ORCH — Hybrid orchestration layer.

Called only when the fast keyword router is uncertain or the request is multi-step.
Returns a routing plan that engine.py executes.
"""
import json
import re

from app.agents.orch_agent import BLACK_ORCH_SYSTEM
from app.audit import logger as audit

# Multi-step trigger phrases — signals that request spans multiple domains
_PIPELINE_SIGNALS = [
    "then", "after that", "and then", "followed by", "step by step",
    "first.*then", "plan for", "help me with.*and", "sequence",
    "workflow", "pipeline", "end to end", "start to finish",
    "from scratch", "full plan", "complete plan", "lay out",
]

# Domains that are ambiguous / frequently mis-routed to "general"
_WEAK_DOMAINS = {"general", "build", "research"}

# Minimum confidence hit to skip ORCH and trust the fast router
_FAST_ROUTER_CONFIDENCE_FLOOR = 2


def needs_orchestration(route: dict, user_input: str) -> bool:
    """
    Returns True if BLACK-ORCH should engage instead of the fast router.
    Conditions:
      1. Fast router landed on 'general' (no keyword match)
      2. Confidence below floor on a weak domain
      3. Request contains multi-step / pipeline signals
    """
    domain = route.get("domain", "general")
    confidence = route.get("confidence", 0)

    if domain == "general":
        return True

    if domain in _WEAK_DOMAINS and confidence < _FAST_ROUTER_CONFIDENCE_FLOOR:
        return True

    text = user_input.lower()
    for signal in _PIPELINE_SIGNALS:
        if re.search(signal, text):
            return True

    return False


def _extract_json(raw: str) -> dict:
    """Pull the first JSON object out of the LLM response."""
    raw = raw.strip()
    # Strip markdown fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to find first {...} block
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {}


_VALID_AGENTS = {
    "finance", "business", "researcher", "builder", "execution",
    "security", "gre", "science", "email", "job_search", "job_apply",
    "ecommerce", "world_intel", "forge", "update_intel",
}


def _sanitize_plan(plan: dict) -> dict:
    """Enforce valid agent names; fall back to researcher on bad values."""
    if plan.get("routing_type") == "single":
        if plan.get("agent") not in _VALID_AGENTS:
            plan["agent"] = "researcher"

    elif plan.get("routing_type") == "pipeline":
        for step in plan.get("steps", []):
            if step.get("agent") not in _VALID_AGENTS:
                step["agent"] = "researcher"

    return plan


def run_orch(user_input: str, fast_route: dict, session_id: str = "") -> dict:
    """
    Call BLACK-ORCH to get an enhanced routing plan.
    Returns a plan dict — engine.py decides how to execute it.

    Falls back to the fast route on any failure so there is no single point of failure.
    """
    from app.services.inference import call_inference

    prompt = (
        f"User request: {user_input}\n\n"
        f"Fast router result (low confidence): domain={fast_route.get('domain')}, "
        f"confidence={fast_route.get('confidence')}, agent={fast_route.get('agent')}\n\n"
        "Determine the correct routing plan. Return only the JSON."
    )

    try:
        raw, provider = call_inference(prompt=prompt, system=BLACK_ORCH_SYSTEM, tier="fast")
        audit.log_event(
            "orch_called",
            {"provider": provider, "raw_preview": raw[:200]},
            session_id=session_id,
        )
    except Exception as exc:
        audit.log_event("orch_failed", {"error": str(exc)}, session_id=session_id)
        return {"routing_type": "single", "agent": fast_route.get("agent", "researcher"),
                "task_type": fast_route.get("task_type", "general"),
                "requires_approval": False, "confidence": "low",
                "reasoning": "ORCH call failed — fast router fallback"}

    plan = _extract_json(raw)
    if not plan:
        audit.log_event("orch_parse_failed", {"raw": raw[:300]}, session_id=session_id)
        return {"routing_type": "single", "agent": fast_route.get("agent", "researcher"),
                "task_type": fast_route.get("task_type", "general"),
                "requires_approval": False, "confidence": "low",
                "reasoning": "ORCH parse failed — fast router fallback"}

    plan = _sanitize_plan(plan)
    audit.log_event(
        "orch_routed",
        {"routing_type": plan.get("routing_type"), "confidence": plan.get("confidence"),
         "reasoning": plan.get("reasoning", "")[:120]},
        session_id=session_id,
    )
    return plan
