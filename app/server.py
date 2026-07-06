"""FastAPI app: event ingress + background poller + observability API/dashboard.

Trigger surfaces (the "event-driven" requirement):
  * POST /webhooks/github   -- real GitHub `issues.labeled` events
  * POST /api/scan          -- run the scanner and dispatch everything it finds
  * POST /api/dispatch/{id} -- dispatch a single known finding on demand

A background task reconciles every open Devin session on an interval, so the
dashboard reflects reality without any manual refresh of state.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from . import metrics, orchestrator, scanner, store
from .config import settings
from .dashboard import render_dashboard
from .issue_format import parse_finding
from .models import Finding

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("sentinel.server")

app = FastAPI(title="Devin Sentinel", version="1.0")


@app.on_event("startup")
async def _startup() -> None:
    store.init_db()
    problems = settings.validate()
    if problems:
        log.warning("config problems: %s", "; ".join(problems))
    asyncio.create_task(_poller_loop())
    log.info("Devin Sentinel up. repo=%s org=%s dry_run=%s",
             settings.github_repo, settings.devin_org_id, settings.dry_run)


async def _poller_loop() -> None:
    while True:
        try:
            n = await asyncio.to_thread(orchestrator.poll_once)
            if n:
                log.info("reconciled %d open session(s)", n)
        except Exception as exc:
            log.warning("poller error: %s", exc)
        await asyncio.sleep(settings.poll_interval_seconds)


# --------------------------------------------------------------------------- #
# Event ingress
# --------------------------------------------------------------------------- #
def _verify_signature(body: bytes, signature: str | None) -> bool:
    if not settings.github_webhook_secret:
        return True  # unsecured mode for local/demo use
    if not signature:
        return False
    mac = hmac.new(settings.github_webhook_secret.encode(), body, hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected, signature)


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    background: BackgroundTasks,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str | None = Header(default=None),
):
    raw = await request.body()
    if not _verify_signature(raw, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="bad signature")

    payload = await request.json()
    if x_github_event != "issues":
        return {"ignored": f"event={x_github_event}"}

    action = payload.get("action")
    issue = payload.get("issue", {})
    labels = [l["name"] for l in issue.get("labels", [])]
    label_name = (payload.get("label") or {}).get("name")

    # Only fire when OUR trigger label is applied.
    fired = action == "labeled" and label_name == settings.trigger_label
    if not fired and not (action in {"opened", "reopened"} and settings.trigger_label in labels):
        return {"ignored": f"action={action} label={label_name}"}

    finding = parse_finding(issue.get("body", ""))
    if finding is None:
        return {"ignored": "no sentinel-finding metadata in issue body"}

    store.log_event("webhook", finding.id, f"issue #{issue.get('number')} labeled")
    orchestrator.ingest(finding, issue_number=issue.get("number"), issue_url=issue.get("html_url", ""))
    background.add_task(orchestrator.dispatch, finding)
    return {"triggered": finding.id, "issue": issue.get("number")}


@app.post("/api/scan")
async def run_scan(background: BackgroundTasks):
    """Scanner trigger: ingest every curated finding and dispatch it to Devin."""
    findings = scanner.load_curated()
    for f in findings:
        orchestrator.ingest(f)
        background.add_task(orchestrator.dispatch, f)
    return {"dispatched": [f.id for f in findings], "count": len(findings)}


@app.post("/api/dispatch/{finding_id}")
async def dispatch_one(finding_id: str, background: BackgroundTasks):
    findings = {f.id: f for f in scanner.load_curated()}
    finding = findings.get(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="unknown finding")
    orchestrator.ingest(finding)
    background.add_task(orchestrator.dispatch, finding)
    return {"dispatched": finding_id}


# --------------------------------------------------------------------------- #
# Observability API
# --------------------------------------------------------------------------- #
@app.get("/api/metrics")
async def api_metrics():
    return metrics.compute()


@app.get("/api/remediations")
async def api_remediations():
    return [r.to_dict() for r in store.all_remediations()]


@app.get("/api/events")
async def api_events():
    return store.recent_events()


@app.post("/api/poll")
async def force_poll():
    return {"reconciled": orchestrator.poll_once()}


@app.get("/healthz")
async def healthz():
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return render_dashboard(
        metrics.compute(), store.all_remediations(), store.recent_events(20)
    )
