# 🛡️ Devin Sentinel — an Engineering Control Plane

**One event-driven control plane that turns raw engineering events into governed, autonomous work — using [Devin](https://docs.devin.ai/api-reference/overview) as the worker.**

Most teams don't have an "AI writes code" problem. They have a **throughput and governance** problem: detection is solved (Dependabot, Snyk, CodeQL, PagerDuty), but the expensive last mile — *actually fixing it, documenting it, and doing it under change-control* — still falls on senior engineers. And the #1 reason an enterprise won't let an autonomous agent merge code is **governance**: audit trails, rollback plans, approvals.

Sentinel is the layer that makes autonomy *adoptable*. Events flow into a central orchestrator; a **rules engine** classifies each one, determines the engineering artifacts the org requires, and dispatches a managed Devin session. The dashboard doesn't just say "task done" — it shows **why the task exists, which policies were satisfied automatically, which still need human approval, and the engineer-time saved.**

### Three workloads on one control plane

| | Workload | Event | Devin produces | Observable output |
|---|---|---|---|---|
| 🛡️ | **Prevent** | Security finding / dependency CVE | The fix + passing tests | Pull request |
| 📋 | **Govern** | Pull request opened | Threat model, rollback plan, ADR, migration plan, security checklist, changelog, tests | PR review + committed docs + status check |
| 🚨 | **Respond** | PagerDuty-style incident alert | Root-cause bisect + rollback | RCA issue + rollback PR + Slack notice |

Demo targets: [`gabrycina/superset`](https://github.com/gabrycina/superset) (a fork of Apache Superset) and [`gabrycina/sentinel-demo-service`](https://github.com/gabrycina/sentinel-demo-service) (a service with a planted regression).

---

## Architecture

```
   EVENTS                      CONTROL PLANE (FastAPI)                    WORKERS         OUTPUTS
 ┌───────────────┐
 │ security find │──┐
 │ dependency    │  │        ┌──────────────┐   ┌───────────────┐   ┌────────────┐   ┌──────────┐
 │ failed CI     │  ├──────▶ │ Rules engine │──▶│  Orchestrator │──▶│  Devin     │──▶│  PRs     │
 │ policy violat.│  │        │ classify +   │   │  dispatch +   │   │  session   │   │  issues  │
 │ pull request  │  │        │ require      │   │  track (SQLite)│   │  per event │   │  docs    │
 │ incident alert│──┘        │ artifacts    │   └───────┬───────┘   └─────┬──────┘   │  Slack   │
 └───────────────┘           └──────────────┘           │  reconcile      │ opens    └──────────┘
                                                          ▼  (poll)        ▼
                                             ┌─────────────────────────────────────┐
                                             │  Dashboard: why · policies auto vs.  │
                                             │  human-approval · ROI / eng-hrs saved│
                                             └─────────────────────────────────────┘
```

Everything is **one shared model** (`Job`) and **one orchestrator**; a workload is just an event source + a prompt + a structured-output schema. The security workload, the governance rules engine, and the incident SRE are the same 900 lines of Python with three prompts.

---

## Quickstart

```bash
cp .env.example .env         # set DEVIN_API_KEY (cog_...), DEVIN_ORG_ID, GITHUB_TOKEN
docker compose up --build    # dashboard on http://localhost:8000
```
Find your Devin org id: `curl -s https://api.devin.ai/v3/self -H "Authorization: Bearer $DEVIN_API_KEY"`.
Local (no Docker): `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/uvicorn app.server:app`.

> **Zero-cost dry run:** `DRY_RUN=true` runs the entire pipeline — every workload, the dashboard, the ROI math — **without spending a single ACU.**

### Triggering each workload

| Workload | Real event | Local simulation |
|---|---|---|
| **Prevent** | Add the `devin-fix` label to a security issue | `python scripts/simulate_event.py 0` · or `curl -X POST localhost:8000/api/scan` |
| **Govern** | Open a pull request | `python scripts/simulate_pr.py <pr_number>` |
| **Respond** | PagerDuty webhook → `/api/incident` | `python scripts/trigger_incident.py` |

Seed the security findings as GitHub issues first with `python scripts/seed_issues.py` (real CVEs from an OSV.dev scan of Superset's dependencies). Run a fresh live scan with `python scripts/scan.py --dispatch`.

---

## Observability — "how would a leader know it's working?"

The dashboard (styled to feel native to Devin) and `/api/metrics` answer it across all workloads:

- **Why each job exists** — the triggering event and the policy that created the work.
- **Policy posture** — for every governed change: which required artifacts Devin satisfied **automatically** vs. which still **need a human sign-off** (threat models and security checklists are always human-approved, by policy).
- **Throughput & success** — jobs in progress, PRs produced, success rate; failures are shown, not hidden.
- **Cost & ROI** — ACUs/$ read straight off each session, engineer-hours saved, and **net value**.

Endpoints: `GET /api/metrics`, `GET /api/jobs`, `GET /api/events`, `POST /api/poll`.

The governance policy itself is config: [`policy.yaml`](policy.yaml) maps change risk-tiers (critical / standard / low) to required artifacts, and lists which artifacts must always be human-approved.

---

## Design decisions that matter

- **Governance as config, not code.** `policy.yaml` encodes the org's change-management policy; the rules engine classifies each PR by the files it touches.
- **Structured output as source of truth.** Every session emits a workload-specific JSON schema, so the dashboard shows authoritative outcomes (and, for governance, *which artifact needs approval*) instead of scraping prose.
- **Truthful failure.** Prompts give Devin permission to stop and report `partial` / `investigating` rather than force a broken PR or a speculative rollback.
- **Idempotent & guarded.** State is keyed on `job_id` (safe to replay events); every session is ACU-capped and tagged so the fleet is isolable and spend is bounded.

---

## Extending in a real customer engagement

- Wire real feeds: Snyk/Trivy/CodeQL → Prevent; branch protection → Govern; PagerDuty/Datadog → Respond.
- Add an approvals workflow: auto-merge low-risk PRs when CI is green; hold criticals for a human `go`.
- Emit an OpenTelemetry `/metrics` endpoint so the customer's existing Grafana/Datadog picks up the fleet with zero new infra (the bespoke ROI view stays for the exec conversation).
- Per-team ACU budgets, concurrency limits, and Devin playbooks that encode each repo's contribution conventions.

See [`LOOM_SCRIPT.md`](LOOM_SCRIPT.md) for the 5-minute pitch walkthrough.
