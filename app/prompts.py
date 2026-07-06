"""Prompt construction for remediation sessions.

The quality of this prompt is what makes Devin behave like an autonomous
teammate rather than an autocomplete. It gives Devin: the repo, the exact
finding, hard acceptance criteria, and the guardrails a senior reviewer would
set before merging.
"""
from __future__ import annotations

from .config import settings
from .models import Finding, Remediation

_TEMPLATE = """\
You are remediating a security/quality finding in the repository `{repo}`
(base branch: `{base}`). Work autonomously and open a pull request.

## Finding
- ID: {fid}
- Source scanner: {source}
- Severity: {severity}
- Package / area: {package}
- CVE: {cve}
- Title: {title}

### Details
{description}

### Suggested fix
{fix_hint}

## What to do
1. Clone `{repo}`, create a branch named `sentinel/{branch}`.
2. Implement the smallest correct change that resolves this specific finding.
   - For a dependency vulnerability: bump the package to `{fixed_version}` (or the
     nearest safe version), and update any lockfiles / constraints so the tree is
     consistent.
   - Adapt call sites only if the upgrade introduces breaking changes.
3. Do NOT bundle unrelated changes. One finding = one focused PR.
4. Run the relevant tests / linters for the code you touched and make them pass.
   If the full suite is too large, run the targeted subset and say so.
5. Open a pull request against `{base}`.
   - Title: `[sentinel] {title}`
   - Body: what the vulnerability was, what you changed, how you verified it,
     and a line `Fixes #{issue_number}` if an issue number is present.

## Acceptance criteria (all required)
- A pull request exists and is linked in your structured output.
- The change is scoped to this finding only.
- You state clearly whether tests passed.

## If you get blocked
If the fix is not safely achievable (e.g. the upgrade cascades into many
breaking changes), STOP, do not force it, and report `outcome: "partial"` or
`"failed"` with a short explanation of the blocker. A correct "I couldn't safely
fix this" is more valuable than a broken PR.

When finished, populate the structured output with the outcome, PR url,
whether tests passed, a one-paragraph summary, and the files you changed.
"""


def build_prompt(finding: Finding, rem: Remediation) -> str:
    fix_hint = "Upgrade the affected package to a non-vulnerable version."
    if finding.fixed_version:
        fix_hint = f"Upgrade `{finding.package}` to `{finding.fixed_version}` or later."
    branch = finding.id.lower().replace("_", "-")[:60]
    return _TEMPLATE.format(
        repo=settings.github_repo,
        base=settings.github_base_branch,
        fid=finding.id,
        source=finding.source,
        severity=finding.severity,
        package=finding.package or "n/a",
        cve=finding.cve or "n/a",
        title=finding.title,
        description=finding.description or "(see scanner reference links)",
        fix_hint=fix_hint,
        fixed_version=finding.fixed_version or "latest safe",
        branch=branch,
        issue_number=rem.issue_number or "",
    )
