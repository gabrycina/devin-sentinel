# 🎬 Loom Script — Devin Sentinel (target: 5:00)

**Audience:** a VP of Engineering + senior ICs evaluating Devin.
**Goal:** land the *detection→remediation gap* thesis, show it working live, and make the "why an autonomous agent" case.

**Before you hit record**
- Server running live: `docker compose up` (or `uvicorn app.server:app`), dashboard open at `localhost:8000`.
- Tabs ready: (1) dashboard, (2) the fork's Issues, (3) one Devin session in the browser, (4) an opened PR, (5) your editor on `app/orchestrator.py` + `app/prompts.py`.
- Have the 3 real sessions already dispatched so a PR is visible (don't wait on Devin live).

---

## 0:00–0:45 — WHAT: the problem (frame it as money, not tech)
> "Every engineering org I walk into has the same thing: a *mountain* of security findings and almost no throughput on fixing them. Dependabot, Snyk, CodeQL — detection is a solved problem. Your team is drowning in alerts. The expensive part is the last mile: someone has to read the CVE, make the change, **run the tests, fix what the upgrade breaks**, and open a reviewable PR. That's senior-engineer hours, times hundreds of findings, and it's why security backlogs never shrink."
>
> "So I built **Devin Sentinel**: an event-driven system where Devin closes that detection-to-remediation gap autonomously. I ran it against a fork of Apache Superset — a real, large Flask + React codebase."

## 0:45–1:30 — the input (show the fork's Issues)
> *(Show Issues tab.)* "These five issues aren't hand-written. I ran a live OSV.dev scan against Superset's actual pinned dependencies and found real, current CVEs — python-multipart with four advisories, a path-traversal in jaraco.context, open-redirects in the frontend's urijs. Each issue carries machine-readable metadata in the body. When I add the **`devin-fix`** label — that's the event."

## 1:30–3:15 — HOW: the system in action + architecture
> *(Switch to dashboard.)* "The label fires a GitHub webhook into a FastAPI orchestrator. For each finding it launches **one Devin session** via the v3 API. Watch the dashboard: findings move `queued → running → PR open → succeeded`, each row linking straight to the Devin session and the PR it opened."
>
> *(Open a Devin session tab.)* "Here's Devin actually doing it — cloning Superset, bumping the package, and this is the key part: **running the tests and fixing the fallout**, not just editing a file."
>
> *(Open the PR.)* "And the output an engineer actually reviews: a focused PR, one finding, tests green, `Fixes #3`."
>
> *(Editor: `prompts.py`, then `orchestrator.py`.)* "Two decisions I want to call out. **One** — the prompt gives Devin hard acceptance criteria *and* permission to fail: if an upgrade cascades into breaking changes, Devin stops and reports `partial`, instead of forcing a broken PR. **Two** — I pass a `structured_output_schema`, so every session returns a machine-readable outcome. The dashboard reflects truth, not scraped text. The whole thing is idempotent on finding-id, so replaying an event never double-dispatches."

## 3:15–4:15 — observability & ROI (this is for the VP)
> *(Back to dashboard KPIs.)* "If you're running the org, here's how you know it's working. Throughput, success rate, cycle time. Cost is read straight off each session — actual ACUs spent. And the number that matters: **net value** — PRs produced times engineer-hours-per-fix times loaded cost, minus Devin spend. Three findings here is a few dollars of Devin against roughly a day of senior-engineer time. That ratio is the entire pitch."

## 4:15–5:00 — WHY Devin + WHEN (next steps)
> "Why does this *need* an autonomous agent? Because the value is entirely in the last mile a script can't do — running tests, fixing breakage, exercising judgment on when *not* to change something. Dependabot opens a PR and hands you the problem; Devin hands you a merged-ready fix."
>
> "In a real engagement I'd wire the trigger to your existing Snyk or CodeQL feed, add a policy layer — auto-dispatch low-risk bumps, require a human 'go' on majors — set per-team ACU budgets, and post results into Slack with auto-merge when CI is green. Same architecture; your scanners, your guardrails. That's Sentinel."

---

### Delivery notes
- **Energy and specificity win.** Name real CVEs and real dollars, not "improved efficiency."
- If a live PR isn't ready on camera, narrate over a completed one — never wait on the agent.
- Keep the editor portions to ~30s total; the evaluators read code after. On camera, sell the *decisions*.
- End on the ROI ratio and "your scanners, your guardrails." That's the FDE close.
