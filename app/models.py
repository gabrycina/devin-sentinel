"""Domain types for the Engineering Control Plane.

A single generic record — `Job` — represents one unit of autonomous work,
regardless of which workload produced it (security / governance / incident).
Workload-specific data lives in the flexible `details` dict, and the governance
`policies` list is what powers the "auto-satisfied vs. needs-human-approval" view.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Workload(str, Enum):
    SECURITY = "security"       # Prevent: vulnerability & dependency remediation
    GOVERNANCE = "governance"   # Govern: policy/compliance artifacts on a change
    INCIDENT = "incident"       # Respond: autonomous incident triage & rollback


class EventType(str, Enum):
    SECURITY_FINDING = "security_finding"
    DEPENDENCY_UPDATE = "dependency_update"
    FAILED_CI = "failed_ci"
    POLICY_VIOLATION = "policy_violation"
    PULL_REQUEST = "pull_request"
    INCIDENT_ALERT = "incident_alert"


class PolicyStatus(str, Enum):
    AUTO_SATISFIED = "auto_satisfied"   # Devin produced the artifact autonomously
    NEEDS_APPROVAL = "needs_approval"   # produced, but a human must sign off
    PENDING = "pending"                 # not yet produced
    FAILED = "failed"                   # could not be produced


class Status(str, Enum):
    """Lifecycle of a job as it flows through the control plane."""

    QUEUED = "queued"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    NEEDS_ATTENTION = "needs_attention"  # blocked, or awaiting human approval
    PR_OPEN = "pr_open"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

    @property
    def is_terminal(self) -> bool:
        return self in {Status.SUCCEEDED, Status.FAILED}


OPEN_STATUSES = [s.value for s in Status if not s.is_terminal]


@dataclass
class Finding:
    """A single issue discovered by a scanner (input to the security workload)."""

    id: str
    source: str
    severity: str
    title: str
    description: str
    ecosystem: str = ""
    package: str = ""
    vulnerable_version: str = ""
    fixed_version: str = ""
    cve: str = ""
    references: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Job:
    """One tracked unit of autonomous work: an event + its Devin session + output."""

    job_id: str                 # stable id (dedupe key)
    workload: str = Workload.SECURITY.value
    event_type: str = EventType.SECURITY_FINDING.value
    severity: str = "medium"
    title: str = ""
    reason: str = ""            # WHY this job exists (shown in the UI)
    source: str = ""

    # GitHub / target context
    repo: str = ""
    issue_number: int | None = None
    issue_url: str = ""

    # Devin session
    session_id: str = ""
    session_url: str = ""
    devin_status: str = ""
    devin_status_detail: str = ""
    acus_consumed: float = 0.0

    # Outcome
    status: str = Status.QUEUED.value
    pr_url: str = ""
    tests_passed: bool | None = None
    summary: str = ""
    error: str = ""

    # Control-plane extras
    policies: list[dict[str, Any]] = field(default_factory=list)  # [{name,status,note}]
    details: dict[str, Any] = field(default_factory=dict)          # workload-specific
    eng_minutes_saved: float = 0.0

    # Timestamps (unix seconds)
    created_at: float = 0.0
    dispatched_at: float | None = None
    completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
