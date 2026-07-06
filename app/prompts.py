"""Prompt construction per workload.

Prompt quality is what makes Devin behave like an autonomous teammate. Each
prompt gives Devin the context, hard acceptance criteria, and the guardrails a
senior reviewer would set — and, crucially, permission to stop and report a
truthful partial/failed result rather than force a bad outcome.
"""
from __future__ import annotations

from typing import Any

from .config import settings
from .models import Finding, Job

# --------------------------------------------------------------------------- #
# Workload 1 — Security remediation
# --------------------------------------------------------------------------- #
_SECURITY = """\
You are remediating a security/quality finding in `{repo}` (base: `{base}`).
Work autonomously and open a pull request.

## Finding
- ID: {fid} | Source: {source} | Severity: {severity}
- Package: {package} | CVE: {cve}
- {title}

{description}

## What to do
1. Clone `{repo}`, branch `sentinel/{branch}`.
2. Make the smallest correct change that resolves THIS finding. For a dependency
   vuln, bump `{package}` to `{fixed_version}` (or nearest safe) and update any
   lockfiles/constraints so the tree stays consistent.
3. One finding = one focused PR. No unrelated changes.
4. Run the relevant tests/linters for what you touched; make them pass.
5. Open a PR against `{base}` titled `[sentinel] {title}`, body explaining the
   vuln, the change, and verification. Add `Fixes #{issue_number}` if present.

If the fix isn't safely achievable (e.g. a major upgrade cascades into breaking
changes), STOP and report outcome `partial`/`failed` with the blocker. A correct
"couldn't safely fix" beats a broken PR.

Populate structured output: outcome, pr_url, tests_passed, summary, files_changed.
"""


def build_security_prompt(finding: Finding, job: Job) -> str:
    branch = finding.id.lower().replace("_", "-")[:60]
    fixed = finding.fixed_version or "latest safe"
    return _SECURITY.format(
        repo=settings.github_repo, base=settings.github_base_branch,
        fid=finding.id, source=finding.source, severity=finding.severity,
        package=finding.package or "n/a", cve=finding.cve or "n/a",
        title=finding.title, description=finding.description,
        fixed_version=fixed, branch=branch, issue_number=job.issue_number or "",
    )


# --------------------------------------------------------------------------- #
# Workload 2 — Change governance (compliance artifacts on a PR)
# --------------------------------------------------------------------------- #
_GOVERNANCE = """\
You are the automated change-governance reviewer for `{repo}`. A pull request
was opened and our policy engine classified it as **{tier}** risk
({tier_description}). Your job is to produce the engineering artifacts this org
requires before such a change can merge — so the author gets an audit-ready
paper trail automatically instead of writing it by hand.

## Pull request
- PR #{pr_number}: {pr_title}
- URL: {pr_url}
- Changed files (sample): {changed_files}

## Required artifacts (produce ALL of them)
{artifact_list}

## What to do
1. Check out PR #{pr_number} and read the diff carefully.
2. For each required artifact, write a concise, specific document grounded in the
   ACTUAL diff (not boilerplate). Commit them to `docs/governance/pr-{pr_number}/`
   on the PR's branch, one markdown file per artifact.
3. Post ONE pull-request review comment summarizing: what the change does, the
   artifacts you generated (with links), and explicitly flag the items that still
   REQUIRE HUMAN APPROVAL: {approval_list}.
4. If the change is missing tests, note exactly what tests should be added.

Do not approve or merge anything. You produce the paper trail; humans decide.

Populate structured output: outcome (`complete`/`partial`/`failed`), the
`artifacts` array (name, path, needs_human_approval), `unmet_requirements`,
`review_comment_posted`, and a summary.
"""


def build_governance_prompt(job: Job, classification: dict[str, Any], pr: dict[str, Any]) -> str:
    descs = classification.get("descriptions", {})
    artifact_list = "\n".join(
        f"- **{a}** — {descs.get(a, a)}" for a in classification["required_artifacts"]
    )
    approval_list = ", ".join(
        p["name"] for p in classification["policies"] if p["needs_human_approval"]
    ) or "none"
    return _GOVERNANCE.format(
        repo=settings.github_repo,
        tier=classification["tier"], tier_description=classification["tier_description"],
        pr_number=pr.get("number", ""), pr_title=pr.get("title", ""),
        pr_url=pr.get("html_url", ""),
        changed_files=", ".join(classification.get("matched_paths", []))[:400] or "n/a",
        artifact_list=artifact_list, approval_list=approval_list,
    )


# --------------------------------------------------------------------------- #
# Workload 3 — Incident response (autonomous SRE)
# --------------------------------------------------------------------------- #
_INCIDENT = """\
You are the on-call SRE agent responding to a production incident in `{repo}`.
Triage it autonomously and prepare a rollback for a human to approve. Speed and
correctness matter — this is paging a human right now.

## Alert
- Service: {service} | Severity: {severity}
- Fired: {fired_at}
- Error: {error}

## Signals available to you
### Recent stack trace
```
{stacktrace}
```
### Recent deploys (most recent first)
{deploys}
### Grafana snapshot
{grafana}

## What to do
1. Clone `{repo}`. Correlate the error and the metric regression against the
   recent deploys to form a hypothesis about which change caused it.
2. Confirm by inspecting the diffs of the suspect commits (use `git log`, `git
   show`, and `git bisect`-style reasoning). Identify the single culprit commit.
3. Open a GitHub issue titled `[INCIDENT] {service}: <root cause>` documenting a
   short RCA: symptom, suspect commit, why, and blast radius.
4. Open a PULL REQUEST that reverts/fixes the culprit commit on a
   `hotfix/<incident>` branch, linked to the RCA issue. Prefer a minimal,
   safe rollback. Do NOT merge it — a human approves.
5. Post a Slack-style incident update (call the notify step if available) with
   the root cause, the rollback PR link, and current status.

If you cannot confidently identify the cause, report outcome `investigating`
with what you ruled out — do not open a speculative rollback.

Populate structured output: outcome, suspect_commit, root_cause, rca_issue_url,
rollback_pr_url, slack_notified, summary.
"""


def build_incident_prompt(job: Job, incident: dict[str, Any]) -> str:
    deploys = "\n".join(
        f"- `{d['sha'][:8]}` {d['message']} ({d.get('deployed_at','')})"
        for d in incident.get("deploys", [])
    ) or "- (none provided)"
    return _INCIDENT.format(
        repo=incident.get("repo", ""),
        service=incident.get("service", "unknown"),
        severity=incident.get("severity", "high"),
        fired_at=incident.get("fired_at", ""),
        error=incident.get("error", ""),
        stacktrace=incident.get("stacktrace", "(none)"),
        deploys=deploys,
        grafana=incident.get("grafana", "(none)"),
    )
