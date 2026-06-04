from app.policy.models import PolicyResult, PolicyVerdict, TrustLevel
from app.policy.rules import ACTION_TRUST_MAP, BLOCKED_PATTERNS, HIGH_RISK_PATTERNS


def evaluate(user_input: str, task_type: str, domain: str = "general") -> PolicyResult:
    text = user_input.lower()

    for pattern in BLOCKED_PATTERNS:
        if pattern in text:
            return PolicyResult(
                verdict=PolicyVerdict.BLOCKED,
                trust_level=TrustLevel.BLOCKED,
                reason=f"Matched blocked pattern: '{pattern}'",
                requires_approval=False,
                blocked=True,
            )

    for pattern in HIGH_RISK_PATTERNS:
        if pattern in text:
            return PolicyResult(
                verdict=PolicyVerdict.PENDING_APPROVAL,
                trust_level=TrustLevel.HIGH_RISK_EXECUTE,
                reason=f"High-risk execution intent detected: '{pattern}'",
                requires_approval=True,
                blocked=False,
            )

    trust_level = ACTION_TRUST_MAP.get(task_type, TrustLevel.READ)

    if trust_level == TrustLevel.LOW_RISK_EXECUTE:
        return PolicyResult(
            verdict=PolicyVerdict.AUTO_APPROVED,
            trust_level=trust_level,
            reason="Pre-approved low-risk execution",
            requires_approval=False,
            blocked=False,
        )

    # READ and DRAFT are always auto-approved
    return PolicyResult(
        verdict=PolicyVerdict.AUTO_APPROVED,
        trust_level=trust_level,
        reason="Within automatic autonomy bounds",
        requires_approval=False,
        blocked=False,
    )
