from app.policy.models import TrustLevel

# Maps router task_type to base trust level
ACTION_TRUST_MAP: dict[str, TrustLevel] = {
    "research": TrustLevel.READ,
    "general": TrustLevel.READ,
    "draft": TrustLevel.DRAFT,
    "action-plan": TrustLevel.DRAFT,  # a plan is a draft, not execution
}

# Never execute — irreversible or destructive, matched against normalized lowercase input
BLOCKED_PATTERNS: list[str] = [
    # Destructive filesystem
    "rm -rf",
    "rm -r /",
    "sudo rm",
    "format drive",
    "wipe all",
    "mkfs",
    "dd if=",
    # Database destruction
    "drop database",
    "drop table",
    "truncate table",
    # Memory destruction
    "delete all memory",
    "delete all conversations",
    # System control
    "sudo shutdown",
    "sudo reboot",
    "sudo halt",
    "pkill -9",
    "killall -9",
    # Credential file access
    "/etc/passwd",
    "/etc/shadow",
    "/etc/sudoers",
    ".ssh/id_rsa",
    ".aws/credentials",
    # Remote code execution pipes
    "curl | bash",
    "curl | sh",
    "wget | bash",
    "wget | sh",
    "| sudo",
    # Privilege escalation
    "chmod 777 /",
    "chown root",
    "sudo su",
    "sudo -i",
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
