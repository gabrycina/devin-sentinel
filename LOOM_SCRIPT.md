# 🎬 Loom Script — Devin Sentinel: an Engineering Control Plane (target: 5:00)

**Audience:** a VP of Engineering + senior ICs evaluating Devin for an enterprise.
**Thesis to land:** the blocker to enterprise autonomy isn't code quality — it's *governance and throughput*. Sentinel is the control plane that makes Devin adoptable, shown across three high-toil workloads.

**Before recording**
- `docker compose up` → app at `localhost:8000` (LIVE, populated). The UI is a React/shadcn control plane: **Overview** (the pipeline), clickable **Prevent / Govern / Respond** views, and a **Rules engine** page.
- Browser tabs ready: (1) the app, (2) a security PR on the fork, (3) the **governed PR #9** with Devin's committed `docs/governance/…` + review comment, (4) the **incident rollback PR #2** on `sentinel-demo-service`, (5) editor on `app/policy.py` + `app/orchestrator.py`.

---

## 0:00–0:40 — WHAT: reframe the problem
> "Most teams don't have an 'AI writes code' problem. They have a throughput and governance problem. Detection is solved — Dependabot, Snyk, PagerDuty all fire perfectly. The expensive part is the last mile: fixing it, *documenting it*, and doing it under change control. And the number-one reason an enterprise won't let an agent merge code is governance — audit trails, rollback plans, approvals."
>
> "So I didn't build a bot. I built an **Engineering Control Plane**: events flow into a central orchestrator, a rules engine decides what's required, and Devin does the work — under policy. Three workloads, one system."

## 0:40–1:10 — the control plane (the protagonist)
> *(Overview.)* "This is the whole system on one screen — and notice how little it throws at you. The hero is the pipeline: event types on the left — security findings, dependency updates, failed CI, incidents — flow into the rules engine, out to three workloads: **Prevent, Govern, Respond.** Every node is live and clickable. The four numbers below aren't 'tasks done' — they're *policies auto-satisfied*, *what still needs a human*, and *net engineering value*. Everything else is one click away."

## 1:10–2:10 — Prevent (security) — the fastest proof
> *(Prevent section → PR on fork.)* "Workload one. I ran a real OSV scan against Superset's dependencies, filed the CVEs as issues, and labeling one dispatches Devin. Here are three real merged-ready PRs. And a detail that matters: the scanner flagged `python-multipart` in one file; Devin found it was actually pinned in another and fixed the real one. That judgment is the whole argument for an agent over a script."

## 2:10–3:20 — Govern (the differentiator) — governance as config
> *(Govern section → PR #9.)* "Workload two, and this is what makes Devin *adoptable* in a bank or a hospital. A PR was opened that touches authentication. The rules engine — this is `policy.yaml` — classified it **critical** and required seven artifacts: threat model, rollback plan, ADR, migration plan, security checklist, changelog, tests."
>
> *(Click the Govern workload → open the PR #9 job. Show the policy checklist in the drawer, then the committed docs + review on GitHub.)* "Devin read the actual diff, generated all seven, committed them to the PR, and posted a review. And here's the payoff — this policy checklist: five are **auto-satisfied**, green. But the threat model and security checklist are amber: **by policy they still require a human sign-off.** That line — *fully autonomous where safe, human-gated where it must be* — is how you say yes to an AI agent in a regulated org. The bureaucracy writes itself; the human still decides."

## 3:20–4:20 — Respond (the wow + the $ pitch)
> *(Respond section → incident.)* "Workload three: 5 SREs into 1. A PagerDuty alert fires — checkout service throwing 500s. Devin gets the stack trace, the Grafana snapshot, and the recent deploys."
>
> *(Show RCA issue + rollback PR on sentinel-demo-service.)* "It correlated the error to the deploy window, **bisected the git history to the exact commit** — a 'perf' change that dropped a null-check, which the tests missed because they never covered guest checkout — opened this root-cause issue, and cut a rollback PR for a human to approve. Ten minutes, unattended, at 3am. That's the MTTR and on-call-cost story a VP buys."

## 4:20–5:00 — WHY Devin + WHEN
> "Why does this need an autonomous agent? Every workload's value is the last mile a script can't do — fix the breakage, generate a threat model from a real diff, bisect and reason about a regression. And it's one control plane: your scanners, your PagerDuty, your `policy.yaml`."
>
> "In a real engagement: wire your Snyk and Datadog in, add auto-merge for green low-risk PRs, hold criticals for human approval, set per-team ACU budgets. Same architecture. That's how Devin goes from 'impressive demo' to 'merges code in production, under governance.'"

---
### Delivery notes
- Spend the most time on **Govern** — auto-satisfied vs. needs-approval is your unique enterprise insight; it's what other applicants won't show.
- Name real things: CVE-2026-53540, the bisected commit, "guest checkout." Specificity sells.
- Never wait on a live agent on camera — narrate over the already-produced PR / RCA / docs.
- Close on: *"your scanners, your PagerDuty, your policy.yaml."*
