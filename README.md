# 🛡️ Devin Sentinel

**An event-driven automation that turns security findings into merged pull requests — autonomously — using the [Devin API](https://docs.devin.ai/api-reference/overview).**

Every engineering org already has world-class *detection* (Dependabot, Snyk, Trivy, CodeQL, OSV). Almost none have *remediation at scale*. 100% of the human toil lives in the gap between **"here is a CVE"** and **"here is a reviewed PR that fixes it and keeps the tests green."** Sentinel closes that gap by treating **Devin as an autonomous remediation worker** that you dispatch, manage, and observe programmatically.

Target repository for this demo: [`apache/superset`](https://github.com/apache/superset) (forked to [`gabrycina/superset`](https://github.com/gabrycina/superset)).

---

## What it does

```
 ┌──────────┐   event    ┌───────────────┐   Devin API    ┌──────────────┐
 │ Scanner  │ ─────────▶ │  Orchestrator │ ─────────────▶ │ Devin session│
 │ (OSV.dev)│  GH issue  │  (FastAPI)    │  create/poll   │  per finding │
 └──────────┘  labeled   └───────┬───────┘                └──────┬───────┘
                                  │ SQLite                        │ opens
                                  ▼                               ▼
                          ┌───────────────┐                ┌──────────────┐
                          │  Dashboard +  │◀───reconcile───│  Pull Request│
                          │  ROI metrics  │   status/PR    │  on the fork │
                          └───────────────┘                └──────────────┘
```

1. **Detect.** A scanner (here, a live [OSV.dev](https://osv.dev) query against Superset's real pinned dependencies) produces findings and files them as GitHub issues.
2. **Trigger.** Applying the `devin-fix` label to an issue emits a `issues.labeled` webhook — the event that drives the system. (A periodic scan or a manual API call are alternative triggers.)
3. **Remediate.** The orchestrator launches one **Devin session per finding** with a structured remediation prompt and a `structured_output_schema`, so Devin returns a machine-readable outcome (`fixed` / `partial` / `failed`, PR url, tests-passed).
4. **Observe.** A background poller reconciles every open session; a live dashboard shows throughput, success rate, ACU spend, and **engineer-hours saved**.

## Why Devin (and not a script)

A dependency bump is trivial *until the upgrade breaks something*. Dependabot opens the PR; a human still has to fix the fallout, run the tests, and adapt call sites. That "last mile" is exactly what an autonomous coding agent does and a script cannot: Devin clones the repo, makes the change, **runs the tests, fixes what breaks, and reports back** — or honestly says "this cascades into breaking changes, I stopped." One finding → one focused, reviewed PR, with no human in the loop until review.

---

## Quickstart

### 1. Configure
```bash
cp .env.example .env
# then edit .env — set DEVIN_API_KEY (cog_...), DEVIN_ORG_ID (org-...),
# GITHUB_TOKEN (gh auth token), GITHUB_REPO.
```
Find your Devin org id:
```bash
curl -s https://api.devin.ai/v3/self -H "Authorization: Bearer $DEVIN_API_KEY"
```

### 2. Run with Docker (recommended)
```bash
docker compose up --build
# dashboard at http://localhost:8000
```

### 2b. Or run locally
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.server:app --reload
```

### 3. Seed the findings as GitHub issues (one-time)
```bash
python scripts/seed_issues.py          # creates issues from findings/superset_findings.json
```

### 4. Trigger a remediation — pick any path

| Path | Command | What it demonstrates |
|---|---|---|
| **Real webhook** | Add the `devin-fix` label to an issue in GitHub (webhook → `/webhooks/github`) | Production event-driven flow |
| **Simulated webhook** | `python scripts/simulate_event.py 0` | The same path, no public URL needed |
| **Scan trigger** | `curl -X POST localhost:8000/api/scan` | Autonomous "scan → dispatch everything" |
| **Live scan** | `python scripts/scan.py --dispatch` | Full loop with a *fresh* OSV scan, no seed file |
| **One finding** | `curl -X POST localhost:8000/api/dispatch/SENTINEL-003-urijs` | On-demand single dispatch |

### 5. Watch it work
Open **http://localhost:8000** — the dashboard auto-refreshes and shows each finding move from `queued → running → PR open → succeeded`, with the Devin session and the resulting PR linked inline.

> **Zero-cost dry run:** set `DRY_RUN=true` to exercise the entire pipeline (events, tracking, dashboard, ROI) **without spending any ACUs** — great for testing and for CI.

---

## Observability — "how would a leader know it's working?"

The dashboard and `/api/metrics` answer that directly:

- **Throughput** — findings tracked, sessions in progress, PRs produced.
- **Success/failure** — success rate over resolved findings; failures are surfaced, not hidden (a truthful "couldn't safely fix" is a first-class outcome).
- **Cycle time** — average dispatch → completion.
- **Cost** — ACUs consumed and $ spend, read straight from each session (`acus_consumed`).
- **ROI** — engineer-hours saved and **net value** = (PRs × hours/finding × loaded eng cost) − Devin spend. All assumptions are configurable in `.env`.

Endpoints: `GET /api/metrics`, `GET /api/remediations`, `GET /api/events`, `POST /api/poll`.

---

## Architecture notes

| File | Responsibility |
|---|---|
| `app/server.py` | FastAPI: event ingress (webhook/scan/manual), background poller, dashboard + JSON API |
| `app/orchestrator.py` | Core control loop: `ingest` → `dispatch` → `reconcile`. Framework-free and unit-testable |
| `app/devin.py` | Typed client for the Devin **v3 organization** API (verified live) |
| `app/scanner.py` | Findings source. Swap in Snyk/Trivy/CodeQL here — the rest is source-agnostic |
| `app/prompts.py` | The remediation prompt with hard acceptance criteria and guardrails |
| `app/store.py` | SQLite persistence, idempotent on `finding_id` (safe to replay events) |
| `app/metrics.py` / `app/dashboard.py` | ROI model + server-rendered dashboard (no build step) |

**Design decisions that matter**

- **Idempotency everywhere.** State is keyed on `finding_id`; replaying a webhook or re-running a scan never double-dispatches.
- **Structured output as the source of truth.** We force a JSON schema on every session so status is authoritative, not scraped from prose.
- **Spend guardrails.** Every session is capped (`max_acu_limit`) and tagged (`sentinel`) so cost is bounded and our fleet is isolable from other org activity.
- **Truthful failure.** The prompt instructs Devin to stop and report `partial`/`failed` rather than force a broken PR — and the dashboard shows those honestly.

---

## Real findings in this demo

Produced by querying OSV.dev against Superset's actual `requirements/*.txt` and `superset-frontend/package.json`:

| Finding | Package | Fix | Severity |
|---|---|---|---|
| SENTINEL-001 | `python-multipart` 0.0.29 → 0.0.31 | 4 CVEs (DoS + param smuggling) | high |
| SENTINEL-002 | `jaraco-context` 6.0.1 → 6.1.0 | path traversal | high |
| SENTINEL-003 | `urijs` 1.19.8 → 1.19.11 (frontend) | 3 CVEs (open redirect) | medium |
| SENTINEL-004 | `pytest` 7.4.4 → 9.0.3 (dev) | insecure tmpdir | medium |
| SENTINEL-005 | `flask` 2.3.3 → 3.1.3 | missing `Vary: Cookie` (hard: major bump) | low |

## Extending in a real customer engagement

- **Real detection feeds:** wire the webhook to Snyk/Trivy/CodeQL/Dependabot alerts instead of a curated file.
- **Policy + approvals:** auto-dispatch low-risk bumps; require a human "go" label for majors.
- **Fleet scale:** concurrency limits, per-team budgets, and retry/backoff around blocked sessions.
- **Close the loop:** post PR + metrics back to Slack/Jira; auto-merge when CI is green and the change is within policy.
- **Devin knowledge/playbooks:** attach repo-specific playbooks so Devin follows the team's contribution conventions.
