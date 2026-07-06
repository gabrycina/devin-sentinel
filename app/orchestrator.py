"""The control plane: events in, managed Devin sessions out, across all workloads.

Framework-free so it can be driven by the webhook handler, a scan script, or a
test. Each workload has a `dispatch_*` entry point; a single workload-aware
`reconcile` folds a live Devin session back onto the shared Job model.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from . import store
from .config import settings
from .devin import DevinClient
from .models import (
    EventType,
    Finding,
    Job,
    PolicyStatus,
    Status,
    Workload,
)
from .prompts import build_governance_prompt, build_incident_prompt, build_security_prompt

log = logging.getLogger("sentinel.orchestrator")

_DEVIN_BLOCKED = {"blocked"}
_DEVIN_FINISHED = {"finished", "completed"}
_DEVIN_DEAD = {"stopped", "expired", "cancelled"}

# Rough per-job engineer-time-saved estimates (minutes), for the ROI view.
_ENG_MIN_SECURITY = 150      # read CVE, fix, run tests, PR
_ENG_MIN_PER_ARTIFACT = 45   # each governance doc, by hand
_ENG_MIN_INCIDENT = 180      # triage, correlate, bisect, rollback, write-up


def _launch(job: Job, prompt: str, tags: list[str]) -> Job:
    """Create (or dry-run) the Devin session for a job and persist it."""
    if job.session_id:
        return job
    if settings.dry_run:
        job.session_id = f"dry-{job.job_id}"
        job.session_url = "https://app.devin.ai/sessions/dry-run"
    else:
        client = DevinClient()
        try:
            resp = client.create_session(
                prompt,
                title=f"[sentinel:{job.workload}] {job.title}"[:120],
                tags=tags,
                workload=job.workload,
            )
        finally:
            client.close()
        job.session_id = resp["session_id"]
        job.session_url = resp.get("url", "")
    job.status = Status.DISPATCHED.value
    job.dispatched_at = time.time()
    store.upsert(job)
    store.log_event("dispatched", job.job_id, f"{job.workload}: session {job.session_id}")
    log.info("dispatched %s (%s) -> %s", job.job_id, job.workload, job.session_id)
    return job


# --------------------------------------------------------------------------- #
# Workload 1 — Security
# --------------------------------------------------------------------------- #
def ingest_finding(finding: Finding, *, issue_number: int | None = None, issue_url: str = "") -> Job:
    job = store.get(finding.id)
    if job is None:
        event = (
            EventType.DEPENDENCY_UPDATE.value
            if finding.ecosystem in {"pip", "npm"}
            else EventType.SECURITY_FINDING.value
        )
        job = Job(
            job_id=finding.id,
            workload=Workload.SECURITY.value,
            event_type=event,
            severity=finding.severity,
            title=finding.title,
            reason=f"{finding.severity.upper()} {finding.cve or 'finding'} in {finding.package or 'code'} "
                   f"detected by {finding.source}",
            source=finding.source,
            repo=settings.github_repo,
            eng_minutes_saved=_ENG_MIN_SECURITY,
            details={"cve": finding.cve, "package": finding.package,
                     "fixed_version": finding.fixed_version},
            created_at=time.time(),
        )
    if issue_number is not None:
        job.issue_number = issue_number
        job.issue_url = issue_url
    store.upsert(job)
    store.log_event("ingested", finding.id, job.reason)
    return job


def dispatch_security(finding: Finding) -> Job:
    job = store.get(finding.id) or ingest_finding(finding)
    return _launch(job, build_security_prompt(finding, job), [finding.severity, finding.ecosystem or "code"])


# --------------------------------------------------------------------------- #
# Workload 2 — Governance
# --------------------------------------------------------------------------- #
def dispatch_governance(pr: dict[str, Any], classification: dict[str, Any]) -> Job:
    job_id = f"gov-{settings.github_repo.split('/')[-1]}-pr{pr.get('number')}"
    job = store.get(job_id)
    if job is None:
        job = Job(
            job_id=job_id,
            workload=Workload.GOVERNANCE.value,
            event_type=EventType.PULL_REQUEST.value,
            severity=classification["tier"],
            title=f"Govern PR #{pr.get('number')}: {pr.get('title','')}"[:120],
            reason=f"PR #{pr.get('number')} classified **{classification['tier']}** "
                   f"({classification['tier_description']}) — requires "
                   f"{len(classification['required_artifacts'])} governance artifacts",
            source="policy-engine",
            repo=settings.github_repo,
            issue_number=pr.get("number"),
            issue_url=pr.get("html_url", ""),
            policies=classification["policies"],
            eng_minutes_saved=_ENG_MIN_PER_ARTIFACT * len(classification["required_artifacts"]),
            details={"tier": classification["tier"], "governed_pr": pr.get("html_url", ""),
                     "required_artifacts": classification["required_artifacts"]},
            created_at=time.time(),
        )
        store.upsert(job)
        store.log_event("ingested", job_id, job.reason)
    return _launch(job, build_governance_prompt(job, classification, pr), [classification["tier"]])


# --------------------------------------------------------------------------- #
# Workload 3 — Incident
# --------------------------------------------------------------------------- #
def dispatch_incident(incident: dict[str, Any]) -> Job:
    job_id = incident.get("id") or f"inc-{int(time.time())}"
    job = store.get(job_id)
    if job is None:
        job = Job(
            job_id=job_id,
            workload=Workload.INCIDENT.value,
            event_type=EventType.INCIDENT_ALERT.value,
            severity=incident.get("severity", "high"),
            title=f"{incident.get('service','service')}: {incident.get('error','')}"[:120],
            reason=f"PagerDuty alert on **{incident.get('service','service')}** — "
                   f"{incident.get('error','')}. Correlate → bisect → rollback.",
            source="pagerduty",
            repo=incident.get("repo", ""),
            eng_minutes_saved=_ENG_MIN_INCIDENT,
            details={"service": incident.get("service"), "alert": incident.get("error"),
                     "deploys": incident.get("deploys", [])},
            created_at=time.time(),
        )
        store.upsert(job)
        store.log_event("ingested", job_id, job.reason)
    return _launch(job, build_incident_prompt(job, incident), [incident.get("service", "svc")])


# --------------------------------------------------------------------------- #
# Reconciliation (workload-aware)
# --------------------------------------------------------------------------- #
def _extract_pr_url(session: dict[str, Any], structured: dict[str, Any], *keys: str) -> str:
    for k in keys:
        if structured.get(k):
            return str(structured[k])
    for pr in session.get("pull_requests") or []:
        if isinstance(pr, str):
            return pr
        if isinstance(pr, dict):
            for key in ("url", "html_url", "pr_url"):
                if pr.get(key):
                    return str(pr[key])
    return ""


def _apply_governance(job: Job, structured: dict[str, Any]) -> str:
    produced = {a.get("name"): a for a in (structured.get("artifacts") or []) if isinstance(a, dict)}
    unmet = set(structured.get("unmet_requirements") or [])
    for pol in job.policies:
        name = pol["name"]
        if name in produced:
            pol["status"] = (
                PolicyStatus.NEEDS_APPROVAL.value if pol.get("needs_human_approval")
                else PolicyStatus.AUTO_SATISFIED.value
            )
            if produced[name].get("path"):
                pol["path"] = produced[name]["path"]
        elif name in unmet:
            pol["status"] = PolicyStatus.FAILED.value
    job.details["artifacts_produced"] = len(produced)
    outcome = str(structured.get("outcome") or "").lower()
    if outcome == "failed":
        return Status.FAILED.value
    # If anything still needs human approval or is unmet, it's not fully done.
    if any(p["status"] in {PolicyStatus.NEEDS_APPROVAL.value, PolicyStatus.PENDING.value,
                            PolicyStatus.FAILED.value} for p in job.policies):
        return Status.NEEDS_ATTENTION.value
    return Status.SUCCEEDED.value


def _apply_incident(job: Job, session: dict[str, Any], structured: dict[str, Any]) -> str:
    for k in ("suspect_commit", "root_cause", "rca_issue_url", "slack_notified"):
        if structured.get(k) is not None:
            job.details[k] = structured[k]
    job.pr_url = _extract_pr_url(session, structured, "rollback_pr_url") or job.pr_url
    outcome = str(structured.get("outcome") or "").lower()
    if outcome == "resolved":
        return Status.SUCCEEDED.value
    if outcome == "mitigated":
        return Status.NEEDS_ATTENTION.value  # rollback PR ready, human merges
    if outcome == "failed":
        return Status.FAILED.value
    return Status.RUNNING.value


def reconcile(job: Job, session: dict[str, Any]) -> Job:
    devin_status = (session.get("status") or "").lower()
    job.devin_status = devin_status
    job.devin_status_detail = session.get("status_detail") or ""
    job.acus_consumed = float(session.get("acus_consumed") or 0.0)

    structured = session.get("structured_output")
    structured = structured if isinstance(structured, dict) else {}
    if structured.get("summary"):
        job.summary = str(structured["summary"])

    outcome = str(structured.get("outcome") or "").lower()

    if job.workload == Workload.GOVERNANCE.value and structured:
        job.status = _apply_governance(job, structured)
    elif job.workload == Workload.INCIDENT.value and structured:
        job.status = _apply_incident(job, session, structured)
    else:  # security
        job.pr_url = _extract_pr_url(session, structured, "pr_url") or job.pr_url
        if "tests_passed" in structured:
            job.tests_passed = bool(structured["tests_passed"])
        if outcome == "fixed":
            job.status = Status.SUCCEEDED.value
        elif outcome in {"failed", "not_applicable", "partial"}:
            job.status = Status.FAILED.value
            job.error = job.summary or f"outcome={outcome}"
        elif devin_status in _DEVIN_BLOCKED:
            job.status = Status.NEEDS_ATTENTION.value
        elif job.pr_url:
            job.status = Status.PR_OPEN.value
        elif devin_status in _DEVIN_FINISHED:
            job.status = Status.PR_OPEN.value if job.pr_url else Status.FAILED.value
        elif devin_status in _DEVIN_DEAD:
            job.status = Status.FAILED.value
            job.error = job.error or f"session ended: {devin_status}"
        else:
            job.status = Status.RUNNING.value

    # generic terminal handling for governance/incident when devin dies early
    if job.status not in {Status.SUCCEEDED.value, Status.FAILED.value} and devin_status in _DEVIN_DEAD:
        if not structured:
            job.status = Status.FAILED.value
            job.error = job.error or f"session ended: {devin_status}"

    if Status(job.status).is_terminal and not job.completed_at:
        job.completed_at = time.time()
    store.upsert(job)
    return job


def poll_once() -> int:
    open_rows = store.open_jobs()
    if not open_rows or settings.dry_run:
        return 0
    client = DevinClient()
    n = 0
    try:
        for job in open_rows:
            try:
                session = client.get_session(job.session_id)
                before = job.status
                reconcile(job, session)
                if job.status != before:
                    store.log_event("status_change", job.job_id, f"{before} → {job.status}")
                n += 1
            except Exception as exc:
                log.warning("poll failed for %s: %s", job.job_id, exc)
    finally:
        client.close()
    return n
