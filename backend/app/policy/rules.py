from app.policy.models import TrustLevel

# Maps router task_type to base trust level
ACTION_TRUST_MAP: dict[str, TrustLevel] = {
    "research": TrustLevel.READ,
    "general": TrustLevel.READ,
    "draft": TrustLevel.DRAFT,
    "action-plan": TrustLevel.DRAFT,  # a plan is a draft, not execution
}

# Never execute — irreversible or destructive, matched against lowercase input
BLOCKED_PATTERNS: list[str] = [
    "rm -rf",
    "drop database",
    "drop table",
    "format drive",
    "wipe all",
    "delete all memory",
    "delete all conversations",
]

# Require explicit owner approval before BLACK proceeds — matched against lowercase input
# Kept specific to avoid false positives on research queries that use the same words
HIGH_RISK_PATTERNS: list[str] = [
    "execute trade",
    "place a trade",
    "place an order",
    "execute order",
    "execute the order",
    "wire transfer",
    "transfer funds",
    "send funds",
    "send money",
    "send payment",
    "deploy to production",
    "push to production",
    "release to prod",
    "publish to",
    "delete account",
    "close account",
    "cancel subscription",
]
