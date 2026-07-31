"""
Pattern learning: reads the audit log to surface usage trends
and approval behavior. No LLM call — pure log analysis.
"""
from collections import Counter

from app.audit.store import read_recent


def get_patterns(sample: int = 500) -> dict:
    """
    Analyse the most recent `sample` audit records.
    Returns domain usage, task type breakdown, and approval stats.
    """
    records = read_recent(limit=sample)

    domain_counts: Counter = Counter()
    task_counts: Counter = Counter()
    approved = 0
    rejected = 0
    executed = 0
    auto_approved = 0

    for rec in records:
        event = rec.get("event_type", "")
        details = rec.get("details", {})

        if event == "intent_classified":
            domain = details.get("domain")
            task = details.get("task_type")
            if domain:
                domain_counts[domain] += 1
            if task:
                task_counts[task] += 1

        elif event == "policy_evaluated":
            verdict = details.get("verdict", "")
            if verdict == "auto_approved":
                auto_approved += 1
            elif verdict == "pending_approval":
                pass  # counted separately below

        elif event in ("approval_approved", "approval_resolved"):
            approved += 1
        elif event in ("approval_rejected",):
            rejected += 1
        elif event in ("approval_executed",):
            executed += 1

    top_domains = [{"domain": d, "count": c} for d, c in domain_counts.most_common(5)]
    top_tasks = [{"task_type": t, "count": c} for t, c in task_counts.most_common(5)]

    total_decisions = approved + rejected
    approval_rate = round(approved / total_decisions * 100) if total_decisions > 0 else None

    return {
        "sample_size": len(records),
        "top_domains": top_domains,
        "top_tasks": top_tasks,
        "approvals": {
            "approved": approved,
            "rejected": rejected,
            "executed": executed,
            "auto_approved": auto_approved,
            "approval_rate_pct": approval_rate,
        },
    }
