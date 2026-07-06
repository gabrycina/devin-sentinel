"""Aggregate metrics for the control-plane dashboard.

Answers "how would an engineering leader know this is working?" across all
workloads: throughput, success, spend, engineer-hours saved, and — for
governance — how many policies were satisfied automatically vs. still need a
human sign-off.
"""
from __future__ import annotations

from typing import Any

from . import store
from .config import settings
from .models import PolicyStatus, Status, Workload

_DELIVERED = {Status.SUCCEEDED.value, Status.PR_OPEN.value, Status.NEEDS_ATTENTION.value}


def compute() -> dict[str, Any]:
    jobs = store.all_jobs()
    total = len(jobs)

    by_status: dict[str, int] = {s.value: 0 for s in Status}
    by_workload: dict[str, dict[str, int]] = {
        w.value: {"total": 0, "delivered": 0, "running": 0} for w in Workload
    }
    for j in jobs:
        by_status[j.status] = by_status.get(j.status, 0) + 1
        wl = by_workload.setdefault(j.workload, {"total": 0, "delivered": 0, "running": 0})
        wl["total"] += 1
        if j.status in _DELIVERED or j.pr_url:
            wl["delivered"] += 1
        if j.status in {Status.RUNNING.value, Status.DISPATCHED.value}:
            wl["running"] += 1

    succeeded = by_status[Status.SUCCEEDED.value]
    failed = by_status[Status.FAILED.value]
    running = by_status[Status.RUNNING.value] + by_status[Status.DISPATCHED.value]
    needs_attention = by_status[Status.NEEDS_ATTENTION.value]
    resolved = succeeded + failed
    prs_produced = sum(1 for j in jobs if j.pr_url)
    success_rate = (succeeded / resolved * 100) if resolved else 0.0
    total_acus = sum(j.acus_consumed for j in jobs)

    # policy posture across governance jobs
    pol_auto = pol_approval = pol_pending = 0
    for j in jobs:
        for p in j.policies:
            st = p.get("status")
            if st == PolicyStatus.AUTO_SATISFIED.value:
                pol_auto += 1
            elif st == PolicyStatus.NEEDS_APPROVAL.value:
                pol_approval += 1
            elif st in {PolicyStatus.PENDING.value, PolicyStatus.FAILED.value}:
                pol_pending += 1

    # engineer time saved: count jobs that actually delivered an output
    eng_minutes = sum(
        j.eng_minutes_saved for j in jobs if (j.status in _DELIVERED or j.pr_url)
    )
    eng_hours_saved = eng_minutes / 60
    labor_value = eng_hours_saved * settings.eng_hourly_cost
    devin_spend = total_acus * settings.acu_usd_cost
    net_value = labor_value - devin_spend

    durations = [j.completed_at - j.dispatched_at for j in jobs
                 if j.completed_at and j.dispatched_at]
    avg_cycle_min = (sum(durations) / len(durations) / 60) if durations else 0.0

    return {
        "total": total,
        "by_status": by_status,
        "by_workload": by_workload,
        "running": running,
        "needs_attention": needs_attention,
        "succeeded": succeeded,
        "failed": failed,
        "resolved": resolved,
        "prs_produced": prs_produced,
        "success_rate": round(success_rate, 1),
        "total_acus": round(total_acus, 2),
        "avg_cycle_min": round(avg_cycle_min, 1),
        "policies_auto": pol_auto,
        "policies_need_approval": pol_approval,
        "policies_pending": pol_pending,
        "eng_hours_saved": round(eng_hours_saved, 1),
        "labor_value_usd": round(labor_value, 0),
        "devin_spend_usd": round(devin_spend, 2),
        "net_value_usd": round(net_value, 0),
    }
