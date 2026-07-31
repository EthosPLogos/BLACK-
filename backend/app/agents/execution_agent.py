from app.agents.verifier import VERIFIER_SYSTEM
from app.audit import logger as audit
from app.execution.resolver import resolve_action
from app.execution.sandbox import run_command
from app.services.inference import call_inference

EXECUTION_SYSTEM = """You are Mr.Black Execution.

You receive the output of an executed command and write a clear, factual summary for the owner.
State what ran, whether it succeeded or failed, and what the output means.
Be concise. Flag errors clearly. Only suggest next steps if the output makes them obvious.
"""


def run_execution(
    user_input: str,
    domain: str,
    task_type: str,
    session_id: str = "",
) -> dict:
    """
    Resolve and execute an approved action.

    Returns:
      {
        "success": bool,
        "action_type": str,   # "shell" | "integration_required" | "unresolved"
        "raw_output": str,
        "summary": str,
        "verifier_verdict": str,
      }
    """
    action = resolve_action(user_input, domain, task_type)
    action_type = action["type"]

    # Non-executable actions — return the explanation immediately
    if action_type in ("integration_required", "unresolved"):
        return {
            "success": False,
            "action_type": action_type,
            "raw_output": "",
            "summary": action["message"],
            "verifier_verdict": "N/A",
        }

    # Shell execution
    result = run_command(
        program=action["program"],
        args=action["args"],
        cwd=action.get("cwd"),
    )

    audit.log_event(
        "execution_ran",
        {
            "program": action["program"],
            "args": action["args"],
            "success": result["success"],
            "returncode": result["returncode"],
            "error": result.get("error"),
        },
        session_id=session_id,
    )

    # Verifier pass on the raw output
    verifier_prompt = (
        f"Review this command execution result for safety and correctness.\n\n"
        f"Command: {action['program']} {' '.join(action['args'])}\n"
        f"Return code: {result['returncode']}\n"
        f"Output:\n{result['output']}\n\n"
        "If the output looks safe and expected, respond with exactly: PASS\n"
        "If there are any concerns, list them concisely."
    )
    verifier_verdict, _ = call_inference(prompt=verifier_prompt, system=VERIFIER_SYSTEM)
    passed = "PASS" in verifier_verdict.upper()

    audit.log_event(
        "execution_verified",
        {"passed": passed, "verdict_preview": verifier_verdict[:200]},
        session_id=session_id,
    )

    # Natural-language summary for the owner
    summary_prompt = (
        f"Summarize this command execution result for the owner.\n\n"
        f"Original request: {user_input}\n"
        f"Command: {action['program']} {' '.join(action['args'])}\n"
        f"Success: {result['success']}\n"
        f"Output:\n{result['output'][:2000]}"
    )
    summary, _ = call_inference(prompt=summary_prompt, system=EXECUTION_SYSTEM)

    return {
        "success": result["success"],
        "action_type": "shell",
        "raw_output": result["output"],
        "summary": summary,
        "verifier_verdict": "PASS" if passed else verifier_verdict[:300],
    }
