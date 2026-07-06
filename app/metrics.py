"""Aggregate metrics for the observability dashboard.

Answers the evaluator's core question: "If I were an engineering leader, how
would I know this is working?" -> throughput, success rate, cycle time, spend,
and engineer-hours saved.
"""
from __future__ import annotations

from typing import Any

from . import store
from .config import settings
from .models import Status


def compute() -> dict[str, Any]:
    rows = store.all_remediations()
    total = len(rows)

    by_status: dict[str, int] = {s.value: 0 for s in Status}
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0) + 1

    succeeded = by_status[Status.SUCCEEDED.value]
    failed = by_status[Status.FAILED.value]
    pr_open = by_status[Status.PR_OPEN.value]
    running = by_status[Status.RUNNING.value] + by_status[Status.DISPATCHED.value]
    resolved = succeeded + failed  # terminal outcomes
    prs_produced = sum(1 for r in rows if r.pr_url)

    success_rate = (succeeded / resolved * 100) if resolved else 0.0
    total_acus = sum(r.acus_consumed for r in rows)

    # cycle time: dispatch -> completion, averaged over terminal rows
    durations = [
        r.completed_at - r.dispatched_at
        for r in rows
        if r.completed_at and r.dispatched_at
    ]
    avg_cycle_min = (sum(durations) / len(durations) / 60) if durations else 0.0

    # ROI: every autonomously-produced PR is engineer time not spent
    eng_hours_saved = prs_produced * settings.eng_hours_per_finding
    labor_value = eng_hours_saved * settings.eng_hourly_cost
    devin_spend = total_acus * settings.acu_usd_cost
    net_value = labor_value - devin_spend

    return {
        "total": total,
        "by_status": by_status,
        "running": running,
        "pr_open": pr_open,
        "succeeded": succeeded,
        "failed": failed,
        "resolved": resolved,
        "prs_produced": prs_produced,
        "success_rate": round(success_rate, 1),
        "total_acus": round(total_acus, 2),
        "avg_cycle_min": round(avg_cycle_min, 1),
        "eng_hours_saved": round(eng_hours_saved, 1),
        "labor_value_usd": round(labor_value, 0),
        "devin_spend_usd": round(devin_spend, 2),
        "net_value_usd": round(net_value, 0),
        "assumptions": {
            "eng_hours_per_finding": settings.eng_hours_per_finding,
            "eng_hourly_cost": settings.eng_hourly_cost,
            "acu_usd_cost": settings.acu_usd_cost,
        },
    }
