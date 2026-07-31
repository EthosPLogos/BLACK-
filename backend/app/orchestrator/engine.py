import uuid
from typing import AsyncIterator

from app.approvals.models import create_approval_record
from app.approvals.store import add_approval
from app.audit import logger as audit
from app.memory.store import add_conversation
from app.orchestrator.black_orch import needs_orchestration, run_orch
from app.orchestrator.chain import resolve_system, run_chain, run_fact_check, run_verifier_audit
from app.orchestrator.context import build_prompt
from app.orchestrator.router import classify_intent
from app.policy.engine import evaluate as policy_evaluate
from app.policy.models import PolicyVerdict
from app.services.inference import OllamaDownError, active_provider, select_tier, stream_inference


def _build_ollama_down_response(reason: str) -> dict:
    return {
        "reply": f"LOCAL MODEL OFFLINE\n\n{reason}",
        "agent": "black",
        "task_type": "halted",
        "memory_used": False,
        "policy_verdict": "halted",
        "approval_id": None,
        "inference_provider": "none",
    }


def _build_blocked_response(reason: str) -> dict:
    return {
        "reply": (
            f"This action is blocked by policy.\n\n"
            f"Reason: {reason}\n\n"
            "If you believe this is in error, review your policy rules."
        ),
        "agent": "black",
        "task_type": "blocked",
        "memory_used": False,
        "policy_verdict": PolicyVerdict.BLOCKED.value,
        "approval_id": None,
        "inference_provider": "none",
    }


def _build_approval_response(record: dict, reason: str) -> dict:
    return {
        "reply": (
            f"This action requires your explicit approval before BLACK proceeds.\n\n"
            f"Intent: {record['user_input']}\n\n"
            f"Reason: {reason}\n\n"
            f"Approval ID: {record['id']}\n\n"
            "Use the approval panel to approve or reject."
        ),
        "agent": "black",
        "task_type": "pending_approval",
        "memory_used": False,
        "policy_verdict": PolicyVerdict.PENDING_APPROVAL.value,
        "approval_id": record["id"],
        "inference_provider": "none",
    }


def _run_pipeline(steps: list[dict], user_input: str, session_id: str) -> dict:
    """
    Execute a BLACK-ORCH pipeline sequentially.
    Each step's output is appended to the next step's prompt so agents can build on each other.
    Returns a synthesized final reply.
    """
    accumulated = f"Original request: {user_input}\n\n"
    step_outputs: list[str] = []

    for step in steps:
        agent_name = step.get("agent", "researcher")
        task_desc = step.get("task", "")
        step_num = step.get("step", "?")

        audit.log_event(
            "pipeline_step_start",
            {"step": step_num, "agent": agent_name, "task": task_desc[:80]},
            session_id=session_id,
        )

        step_prompt = f"{accumulated}Now handle step {step_num}: {task_desc}"
        prompt, _ = build_prompt(step_prompt, domain=agent_name)

        try:
            result = run_chain(
                agent_name=agent_name,
                task_type="research",
                domain=agent_name,
                prompt=prompt,
                session_id=session_id,
                user_input=step_prompt,
                tier="frontier",
            )
        except OllamaDownError as exc:
            return _build_ollama_down_response(str(exc))

        step_output = result["reply"]
        step_outputs.append(f"[Step {step_num} — {agent_name}]\n{step_output}")
        accumulated += f"\nStep {step_num} ({agent_name}) result:\n{step_output}\n"

        audit.log_event(
            "pipeline_step_done",
            {"step": step_num, "agent": agent_name, "reply_len": len(step_output)},
            session_id=session_id,
        )

    # Synthesize all step outputs into one coherent response
    synthesis_prompt = (
        f"You assembled the following multi-step outputs for the user's request:\n\n"
        f"{chr(10).join(step_outputs)}\n\n"
        f"Original request: {user_input}\n\n"
        "Synthesize these into a single, clear, actionable response for the owner. "
        "Preserve the key findings from each step. Remove redundancy. "
        "Present as a unified answer, not a list of raw step outputs."
    )

    from app.agents.researcher import RESEARCHER_SYSTEM
    from app.services.inference import call_inference
    final_reply, provider = call_inference(
        prompt=synthesis_prompt, system=RESEARCHER_SYSTEM, tier="frontier"
    )

    audit.log_event(
        "pipeline_synthesized",
        {"steps": len(steps), "final_len": len(final_reply), "provider": provider},
        session_id=session_id,
    )

    return {"reply": final_reply, "agent": "black-orch", "provider": provider}


def run_black(user_input: str, background_tasks=None) -> dict:
    """Synchronous path — used by POST /api/chat."""
    session_id = uuid.uuid4().hex[:8]

    route = classify_intent(user_input)
    audit.log_event(
        "intent_classified",
        {"agent": route["agent"], "task_type": route["task_type"],
         "domain": route["domain"], "input_preview": user_input[:60]},
        session_id=session_id,
    )

    # ── BLACK-ORCH hybrid: engage when fast router is uncertain or request is multi-step ──
    orch_plan = None
    if needs_orchestration(route, user_input):
        orch_plan = run_orch(user_input, route, session_id=session_id)
        audit.log_event(
            "orch_engaged",
            {"routing_type": orch_plan.get("routing_type"),
             "confidence": orch_plan.get("confidence")},
            session_id=session_id,
        )

        # ORCH blocked the request on policy grounds
        if orch_plan.get("routing_type") == "blocked":
            return _build_blocked_response(orch_plan.get("reasoning", "Blocked by BLACK-ORCH policy."))

        # ORCH says approval needed
        if orch_plan.get("requires_approval"):
            record = create_approval_record(
                user_input=user_input,
                policy_reason=orch_plan.get("reasoning", "HIGH-RISK action flagged by BLACK-ORCH"),
                trust_level="medium",
                domain=route["domain"],
                task_type=route.get("task_type", "action-plan"),
                session_id=session_id,
            )
            add_approval(record)
            audit.log_event(
                "orch_approval_required",
                {"approval_id": record["id"], "reasoning": orch_plan.get("reasoning", "")[:120]},
                session_id=session_id,
            )
            return _build_approval_response(record, orch_plan.get("reasoning", "HIGH-RISK action"))

        # Override fast route with ORCH's single-agent decision
        if orch_plan.get("routing_type") == "single":
            route["agent"] = orch_plan.get("agent", route["agent"])
            route["task_type"] = orch_plan.get("task_type", route["task_type"])
            route["domain"] = orch_plan.get("agent", route["domain"])

    # ── Standard policy gate (applies to both fast-route and ORCH single-agent) ──
    policy = policy_evaluate(user_input, route["task_type"], route["domain"])
    audit.log_event(
        "policy_evaluated",
        {"verdict": policy.verdict.value, "trust_level": policy.trust_level.value,
         "reason": policy.reason},
        session_id=session_id,
    )

    if policy.blocked:
        audit.log_event("blocked", {"reason": policy.reason}, session_id=session_id)
        return _build_blocked_response(policy.reason)

    if policy.requires_approval:
        record = create_approval_record(
            user_input=user_input,
            policy_reason=policy.reason,
            trust_level=policy.trust_level.value,
            domain=route["domain"],
            task_type=route["task_type"],
            session_id=session_id,
        )
        add_approval(record)
        audit.log_event(
            "approval_required",
            {"approval_id": record["id"], "reason": policy.reason,
             "trust_level": policy.trust_level.value, "input_preview": user_input[:60]},
            session_id=session_id,
        )
        return _build_approval_response(record, policy.reason)

    # ── ORCH pipeline path ────────────────────────────────────────────────────────
    if orch_plan and orch_plan.get("routing_type") == "pipeline":
        _, memory_used = build_prompt(user_input, domain="general")
        result = _run_pipeline(orch_plan["steps"], user_input, session_id)
        if "LOCAL MODEL OFFLINE" in result.get("reply", ""):
            return result
        add_conversation(user_input, result["reply"])
        fact_check = run_fact_check(user_input, result["reply"], "research", session_id)
        return {
            "reply": result["reply"],
            "agent": "black-orch",
            "task_type": "pipeline",
            "memory_used": memory_used,
            "policy_verdict": PolicyVerdict.AUTO_APPROVED.value,
            "approval_id": None,
            "inference_provider": result["provider"],
            "fact_check": fact_check,
            "pipeline_steps": [s.get("agent") for s in orch_plan["steps"]],
        }

    # ── Standard single-agent path ────────────────────────────────────────────────
    tier = select_tier(route["task_type"], route["domain"], user_input)
    prompt, memory_used = build_prompt(user_input, domain=route["domain"])
    audit.log_event(
        "agent_invoked",
        {"agent": route["agent"], "task_type": route["task_type"], "domain": route["domain"], "tier": tier},
        session_id=session_id,
    )

    try:
        result = run_chain(
            agent_name=route["agent"],
            task_type=route["task_type"],
            domain=route["domain"],
            prompt=prompt,
            session_id=session_id,
            user_input=user_input,
            tier=tier,
        )
    except OllamaDownError as exc:
        audit.log_event("ollama_down_halted", {"reason": str(exc)}, session_id=session_id)
        return _build_ollama_down_response(str(exc))

    add_conversation(user_input, result["reply"])
    audit.log_event("conversation_stored", {}, session_id=session_id)

    fact_check = run_fact_check(
        user_input, result["reply"], route["task_type"], session_id,
    )

    if background_tasks is not None and route["task_type"] in {"draft", "action-plan"}:
        background_tasks.add_task(
            run_verifier_audit, user_input, result["reply"], route["task_type"], session_id
        )

    return {
        "reply": result["reply"],
        "agent": result["agent"],
        "task_type": route["task_type"],
        "memory_used": memory_used,
        "policy_verdict": PolicyVerdict.AUTO_APPROVED.value,
        "approval_id": None,
        "inference_provider": result["provider"],
        "fact_check": fact_check,
    }


async def stream_black(user_input: str) -> AsyncIterator[dict]:
    """Async streaming path — used by POST /api/chat/stream."""
    session_id = uuid.uuid4().hex[:8]

    route = classify_intent(user_input)
    audit.log_event(
        "intent_classified",
        {"agent": route["agent"], "task_type": route["task_type"],
         "domain": route["domain"], "input_preview": user_input[:60], "path": "stream"},
        session_id=session_id,
    )

    policy = policy_evaluate(user_input, route["task_type"], route["domain"])
    audit.log_event(
        "policy_evaluated",
        {"verdict": policy.verdict.value, "trust_level": policy.trust_level.value,
         "reason": policy.reason},
        session_id=session_id,
    )

    if policy.blocked:
        audit.log_event("blocked", {"reason": policy.reason}, session_id=session_id)
        yield {"type": "blocked", **_build_blocked_response(policy.reason)}
        return

    if policy.requires_approval:
        record = create_approval_record(
            user_input=user_input,
            policy_reason=policy.reason,
            trust_level=policy.trust_level.value,
            domain=route["domain"],
            task_type=route["task_type"],
            session_id=session_id,
        )
        add_approval(record)
        audit.log_event(
            "approval_required",
            {"approval_id": record["id"], "reason": policy.reason,
             "trust_level": policy.trust_level.value, "input_preview": user_input[:60]},
            session_id=session_id,
        )
        yield {"type": "pending_approval", **_build_approval_response(record, policy.reason)}
        return

    tier = select_tier(route["task_type"], route["domain"], user_input)
    prompt, memory_used = build_prompt(user_input, domain=route["domain"])
    system, effective_agent = resolve_system(route["agent"], route["domain"], user_input)

    provider = active_provider(tier)

    audit.log_event(
        "agent_invoked",
        {"agent": effective_agent, "task_type": route["task_type"],
         "domain": route["domain"], "path": "stream", "provider": provider, "tier": tier},
        session_id=session_id,
    )

    collected: list[str] = []
    try:
        async for token in stream_inference(prompt=prompt, system=system, tier=tier):
            collected.append(token)
            yield {"type": "token", "content": token}
    except RuntimeError as exc:
        yield {"type": "error", "content": str(exc)}
        return

    complete_reply = "".join(collected)
    audit.log_event(
        "inference_completed",
        {"agent": effective_agent, "reply_length": len(complete_reply),
         "path": "stream", "provider": provider},
        session_id=session_id,
    )

    add_conversation(user_input, complete_reply)
    audit.log_event("conversation_stored", {}, session_id=session_id)

    yield {
        "type": "done",
        "agent": effective_agent,
        "task_type": route["task_type"],
        "memory_used": memory_used,
        "policy_verdict": PolicyVerdict.AUTO_APPROVED.value,
        "approval_id": None,
        "inference_provider": provider,
    }

    fact_check = run_fact_check(
        user_input, complete_reply, route["task_type"], session_id,
    )
    yield {"type": "fact_check", **fact_check}
