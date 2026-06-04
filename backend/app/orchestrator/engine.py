import uuid
from typing import AsyncIterator

from app.approvals.models import create_approval_record
from app.approvals.store import add_approval
from app.audit import logger as audit
from app.memory.store import add_conversation
from app.orchestrator.chain import resolve_system, run_chain, run_verifier_audit
from app.orchestrator.context import build_prompt
from app.orchestrator.router import classify_intent
from app.policy.engine import evaluate as policy_evaluate
from app.policy.models import PolicyVerdict
from app.services.inference import active_provider, stream_inference


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


def run_black(user_input: str, background_tasks=None) -> dict:
    """Synchronous path — used by POST /api/chat."""
    session_id = uuid.uuid4().hex[:8]

    route = classify_intent(user_input)
    audit.log_event(
        "intent_classified",
        {"agent": route["agent"], "task_type": route["task_type"],
         "domain": route["domain"], "input_preview": user_input[:120]},
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
             "trust_level": policy.trust_level.value, "input_preview": user_input[:200]},
            session_id=session_id,
        )
        return _build_approval_response(record, policy.reason)

    prompt, memory_used = build_prompt(user_input)
    audit.log_event(
        "agent_invoked",
        {"agent": route["agent"], "task_type": route["task_type"], "domain": route["domain"]},
        session_id=session_id,
    )

    result = run_chain(
        agent_name=route["agent"],
        task_type=route["task_type"],
        domain=route["domain"],
        prompt=prompt,
        session_id=session_id,
        user_input=user_input,
    )

    add_conversation(user_input, result["reply"])
    audit.log_event("conversation_stored", {}, session_id=session_id)

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
    }


async def stream_black(user_input: str) -> AsyncIterator[dict]:
    """Async streaming path — used by POST /api/chat/stream."""
    session_id = uuid.uuid4().hex[:8]

    route = classify_intent(user_input)
    audit.log_event(
        "intent_classified",
        {"agent": route["agent"], "task_type": route["task_type"],
         "domain": route["domain"], "input_preview": user_input[:120], "path": "stream"},
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
             "trust_level": policy.trust_level.value, "input_preview": user_input[:200]},
            session_id=session_id,
        )
        yield {"type": "pending_approval", **_build_approval_response(record, policy.reason)}
        return

    prompt, memory_used = build_prompt(user_input)
    system, effective_agent = resolve_system(route["agent"], route["domain"], user_input)

    # Determine provider before streaming so the done event has accurate metadata.
    # active_provider() uses the same 30s-cached probe as stream_inference internaly.
    provider = active_provider()

    audit.log_event(
        "agent_invoked",
        {"agent": effective_agent, "task_type": route["task_type"],
         "domain": route["domain"], "path": "stream", "provider": provider},
        session_id=session_id,
    )

    collected: list[str] = []
    try:
        async for token in stream_inference(prompt=prompt, system=system):
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
