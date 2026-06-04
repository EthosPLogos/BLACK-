import uuid
from datetime import datetime, timezone

PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"
EXECUTED = "executed"


def create_approval_record(
    user_input: str,
    policy_reason: str,
    trust_level: str,
    domain: str,
    task_type: str,
    session_id: str,
) -> dict:
    return {
        "id": uuid.uuid4().hex[:12],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": PENDING,
        "resolved_at": None,
        "executed_at": None,
        "execution_result": None,
        "user_input": user_input,
        "policy_reason": policy_reason,
        "trust_level": trust_level,
        "domain": domain,
        "task_type": task_type,
        "session_id": session_id,
    }
