from dataclasses import dataclass
from enum import Enum


class TrustLevel(str, Enum):
    READ = "read"
    DRAFT = "draft"
    LOW_RISK_EXECUTE = "low_risk_execute"
    HIGH_RISK_EXECUTE = "high_risk_execute"
    BLOCKED = "blocked"


class PolicyVerdict(str, Enum):
    AUTO_APPROVED = "auto_approved"
    PENDING_APPROVAL = "pending_approval"
    BLOCKED = "blocked"


@dataclass
class PolicyResult:
    verdict: PolicyVerdict
    trust_level: TrustLevel
    reason: str
    requires_approval: bool
    blocked: bool
