"""Domain types for the remediation pipeline."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Status(str, Enum):
    """Lifecycle of a single finding as it flows through the pipeline."""

    QUEUED = "queued"            # finding ingested, not yet handed to Devin
    DISPATCHED = "dispatched"    # Devin session created
    RUNNING = "running"          # Devin actively working
    NEEDS_ATTENTION = "needs_attention"  # Devin blocked, waiting on a human
    PR_OPEN = "pr_open"          # Devin opened a pull request
    SUCCEEDED = "succeeded"      # remediated (outcome=fixed)
    FAILED = "failed"            # Devin could not remediate

    @property
    def is_terminal(self) -> bool:
        return self in {Status.SUCCEEDED, Status.FAILED}


# Statuses the poller should keep polling on.
OPEN_STATUSES = [s.value for s in Status if not s.is_terminal]


@dataclass
class Finding:
    """A single issue discovered by a scanner (the input to the pipeline)."""

    id: str                     # stable id, e.g. "PIP-AUDIT-jinja2-CVE-2024-22195"
    source: str                 # scanner name
    severity: str               # critical | high | medium | low
    title: str
    description: str
    ecosystem: str = ""         # pip | npm | code
    package: str = ""
    vulnerable_version: str = ""
    fixed_version: str = ""
    cve: str = ""
    references: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Remediation:
    """One tracked unit of work: a finding + its Devin session + its PR."""

    finding_id: str
    source: str
    severity: str
    title: str
    package: str = ""
    cve: str = ""
    status: str = Status.QUEUED.value

    # GitHub issue
    issue_number: int | None = None
    issue_url: str = ""

    # Devin session
    session_id: str = ""
    session_url: str = ""
    devin_status: str = ""
    devin_status_detail: str = ""
    acus_consumed: float = 0.0

    # Outcome
    pr_url: str = ""
    tests_passed: bool | None = None
    summary: str = ""
    error: str = ""

    # Timestamps (unix seconds)
    created_at: float = 0.0
    dispatched_at: float | None = None
    completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
