"""The core control loop: findings in, managed Devin sessions out.

Responsibilities:
  * ingest a Finding into the store (idempotent on finding_id),
  * dispatch a Devin session with a well-formed remediation prompt,
  * reconcile a live Devin session's raw state onto our own lifecycle Status.

This module is intentionally free of any web/framework code so it can be driven
equally by the webhook handler, the scan script, or a test.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from . import store
from .config import settings
from .devin import DevinClient
from .models import Finding, Remediation, Status
from .prompts import build_prompt

log = logging.getLogger("sentinel.orchestrator")

# How we translate Devin's raw session vocabulary into ours.
_DEVIN_BLOCKED = {"blocked"}
_DEVIN_FINISHED = {"finished", "completed"}
_DEVIN_DEAD = {"stopped", "expired", "cancelled"}


def ingest(finding: Finding, *, issue_number: int | None = None, issue_url: str = "") -> Remediation:
    """Create or update the tracking row for a finding without dispatching."""
    rem = store.get(finding.id)
    if rem is None:
        rem = Remediation(
            finding_id=finding.id,
            source=finding.source,
            severity=finding.severity,
            title=finding.title,
            package=finding.package,
            cve=finding.cve,
            created_at=time.time(),
        )
    if issue_number is not None:
        rem.issue_number = issue_number
        rem.issue_url = issue_url
    store.upsert(rem)
    store.log_event("ingested", finding.id, f"{finding.severity.upper()}: {finding.title}")
    return rem


def dispatch(finding: Finding) -> Remediation:
    """Launch (or reuse) a Devin session for a finding. Idempotent."""
    rem = store.get(finding.id) or ingest(finding)

    if rem.session_id:
        log.info("finding %s already dispatched to %s", finding.id, rem.session_id)
        return rem

    prompt = build_prompt(finding, rem)

    if settings.dry_run:
        rem.session_id = f"dry-{finding.id}"
        rem.session_url = "https://app.devin.ai/sessions/dry-run"
        rem.status = Status.DISPATCHED.value
        rem.dispatched_at = time.time()
        store.upsert(rem)
        store.log_event("dispatched", finding.id, "DRY_RUN: no real session created")
        return rem

    client = DevinClient()
    try:
        resp = client.create_session(
            prompt,
            title=f"[sentinel] {finding.title}"[:120],
            tags=[finding.severity, finding.ecosystem or "code"],
        )
    finally:
        client.close()

    rem.session_id = resp["session_id"]
    rem.session_url = resp.get("url", "")
    rem.status = Status.DISPATCHED.value
    rem.dispatched_at = time.time()
    store.upsert(rem)
    store.log_event("dispatched", finding.id, f"session {rem.session_id}")
    log.info("dispatched %s -> %s", finding.id, rem.session_id)
    return rem


def _extract_pr_url(session: dict[str, Any], structured: dict[str, Any]) -> str:
    if structured.get("pr_url"):
        return str(structured["pr_url"])
    prs = session.get("pull_requests") or []
    for pr in prs:
        if isinstance(pr, str):
            return pr
        if isinstance(pr, dict):
            for key in ("url", "html_url", "pr_url"):
                if pr.get(key):
                    return str(pr[key])
    return ""


def reconcile(rem: Remediation, session: dict[str, Any]) -> Remediation:
    """Fold a fresh Devin session payload into our tracked Remediation."""
    devin_status = (session.get("status") or "").lower()
    rem.devin_status = devin_status
    rem.devin_status_detail = session.get("status_detail") or ""
    rem.acus_consumed = float(session.get("acus_consumed") or 0.0)

    structured = session.get("structured_output") or {}
    if not isinstance(structured, dict):
        structured = {}

    pr_url = _extract_pr_url(session, structured)
    if pr_url:
        rem.pr_url = pr_url
    if "tests_passed" in structured:
        rem.tests_passed = bool(structured["tests_passed"])
    if structured.get("summary"):
        rem.summary = str(structured["summary"])

    outcome = str(structured.get("outcome") or "").lower()

    # --- decide our lifecycle status (authoritative signals win) ------------
    if outcome == "fixed":
        rem.status = Status.SUCCEEDED.value
        rem.completed_at = rem.completed_at or time.time()
    elif outcome in {"failed", "not_applicable", "partial"}:
        rem.status = Status.FAILED.value
        rem.error = rem.summary or f"Devin reported outcome={outcome}"
        rem.completed_at = rem.completed_at or time.time()
    elif devin_status in _DEVIN_BLOCKED:
        rem.status = Status.NEEDS_ATTENTION.value
    elif rem.pr_url:
        rem.status = Status.PR_OPEN.value
    elif devin_status in _DEVIN_FINISHED:
        rem.status = Status.PR_OPEN.value if rem.pr_url else Status.FAILED.value
        rem.completed_at = rem.completed_at or time.time()
    elif devin_status in _DEVIN_DEAD:
        rem.status = Status.FAILED.value
        rem.error = rem.error or f"session ended: {devin_status}"
        rem.completed_at = rem.completed_at or time.time()
    else:
        rem.status = Status.RUNNING.value

    store.upsert(rem)
    return rem


def poll_once() -> int:
    """Reconcile every open remediation against Devin. Returns count polled."""
    open_rows = store.open_remediations()
    if not open_rows or settings.dry_run:
        return 0
    client = DevinClient()
    n = 0
    try:
        for rem in open_rows:
            try:
                session = client.get_session(rem.session_id)
                before = rem.status
                reconcile(rem, session)
                if rem.status != before:
                    store.log_event(
                        "status_change", rem.finding_id, f"{before} -> {rem.status}"
                    )
                n += 1
            except Exception as exc:  # keep the loop alive on a single bad session
                log.warning("poll failed for %s: %s", rem.finding_id, exc)
    finally:
        client.close()
    return n
