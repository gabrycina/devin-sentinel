"""FastAPI control plane: multi-workload event ingress + poller + dashboard.

Event surfaces:
  * POST /webhooks/github    -- issues.labeled  -> Security ; pull_request.opened -> Govern
  * POST /api/incident       -- PagerDuty-style alert -> Respond
  * POST /api/scan           -- run the scanner and dispatch every finding
  * POST /api/dispatch/{id}  -- dispatch a single known finding
A background task reconciles every open Devin session across all workloads.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging

from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from . import github_client, metrics, orchestrator, policy, scanner, store
from .config import settings
from .dashboard import render_dashboard
from .issue_format import parse_finding

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("sentinel.server")

app = FastAPI(title="Devin Sentinel — Engineering Control Plane", version="2.0")


@app.on_event("startup")
async def _startup() -> None:
    store.init_db()
    if problems := settings.validate():
        log.warning("config problems: %s", "; ".join(problems))
    asyncio.create_task(_poller_loop())
    log.info("Sentinel up. repo=%s org=%s dry_run=%s", settings.github_repo,
             settings.devin_org_id, settings.dry_run)


async def _poller_loop() -> None:
    while True:
        try:
            if n := await asyncio.to_thread(orchestrator.poll_once):
                log.info("reconciled %d open session(s)", n)
        except Exception as exc:
            log.warning("poller error: %s", exc)
        await asyncio.sleep(settings.poll_interval_seconds)


# --------------------------------------------------------------------------- #
# Event ingress
# --------------------------------------------------------------------------- #
def _verify(body: bytes, sig: str | None) -> bool:
    if not settings.github_webhook_secret:
        return True
    if not sig:
        return False
    mac = hmac.new(settings.github_webhook_secret.encode(), body, hashlib.sha256)
    return hmac.compare_digest("sha256=" + mac.hexdigest(), sig)


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    background: BackgroundTasks,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str | None = Header(default=None),
):
    raw = await request.body()
    if not _verify(raw, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="bad signature")
    payload = await request.json()

    # --- Security workload: issue labeled with the trigger label -------------
    if x_github_event == "issues":
        issue = payload.get("issue", {})
        labels = [l["name"] for l in issue.get("labels", [])]
        label_name = (payload.get("label") or {}).get("name")
        fired = payload.get("action") == "labeled" and label_name == settings.trigger_label
        if not fired and settings.trigger_label not in labels:
            return {"ignored": f"action={payload.get('action')} label={label_name}"}
        finding = parse_finding(issue.get("body", ""))
        if finding is None:
            return {"ignored": "no sentinel-finding metadata"}
        store.log_event("webhook", finding.id, f"issue #{issue.get('number')} labeled")
        orchestrator.ingest_finding(finding, issue_number=issue.get("number"),
                                    issue_url=issue.get("html_url", ""))
        background.add_task(orchestrator.dispatch_security, finding)
        return {"triggered": finding.id, "workload": "security"}

    # --- Govern workload: PR opened ------------------------------------------
    if x_github_event == "pull_request":
        if payload.get("action") not in {"opened", "reopened", "ready_for_review"}:
            return {"ignored": f"action={payload.get('action')}"}
        pr = payload.get("pull_request", {})
        number = pr.get("number")
        try:
            files = github_client.get_pr_files(number)
        except Exception as exc:
            log.warning("could not fetch PR files: %s", exc)
            files = [f["filename"] for f in payload.get("pull_request", {}).get("files", [])]
        classification = policy.classify(files or ["unknown"])
        store.log_event("webhook", f"pr{number}",
                        f"PR #{number} → tier={classification['tier']}")
        background.add_task(orchestrator.dispatch_governance,
                            {"number": number, "title": pr.get("title", ""),
                             "html_url": pr.get("html_url", "")}, classification)
        return {"triggered": f"pr{number}", "workload": "governance",
                "tier": classification["tier"], "required": classification["required_artifacts"]}

    return {"ignored": f"event={x_github_event}"}


@app.post("/api/incident")
async def incident(request: Request, background: BackgroundTasks):
    """Respond workload: PagerDuty-style alert -> autonomous SRE session."""
    payload = await request.json()
    payload.setdefault("repo", settings.incident_repo)
    store.log_event("incident", payload.get("id", ""),
                    f"alert: {payload.get('service')} — {payload.get('error','')}")
    background.add_task(orchestrator.dispatch_incident, payload)
    return {"triggered": payload.get("id"), "workload": "incident"}


@app.post("/api/scan")
async def run_scan(background: BackgroundTasks):
    findings = scanner.load_curated()
    for f in findings:
        orchestrator.ingest_finding(f)
        background.add_task(orchestrator.dispatch_security, f)
    return {"dispatched": [f.id for f in findings], "count": len(findings)}


@app.post("/api/dispatch/{finding_id}")
async def dispatch_one(finding_id: str, background: BackgroundTasks):
    finding = {f.id: f for f in scanner.load_curated()}.get(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="unknown finding")
    orchestrator.ingest_finding(finding)
    background.add_task(orchestrator.dispatch_security, finding)
    return {"dispatched": finding_id}


# --------------------------------------------------------------------------- #
# Observability API + dashboard
# --------------------------------------------------------------------------- #
@app.get("/api/metrics")
async def api_metrics():
    return metrics.compute()


@app.get("/api/jobs")
async def api_jobs():
    return [j.to_dict() for j in store.all_jobs()]


@app.get("/api/events")
async def api_events():
    return store.recent_events()


@app.get("/api/rules")
async def api_rules():
    p = policy.load_policy()
    return {**p, "repo": settings.github_repo}


@app.get("/api/config")
async def api_config():
    return {
        "mode": "DRY RUN" if settings.dry_run else "LIVE",
        "repo": settings.github_repo,
        "incident_repo": settings.incident_repo,
    }


@app.post("/api/poll")
async def force_poll():
    return {"reconciled": orchestrator.poll_once()}


@app.get("/healthz")
async def healthz():
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Serve the built React SPA (falls back to the server-rendered page if unbuilt)
# --------------------------------------------------------------------------- #
if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/{full_path:path}", response_class=HTMLResponse)
async def spa(full_path: str):
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return HTMLResponse(render_dashboard(metrics.compute(), store.all_jobs(), store.recent_events(20)))
