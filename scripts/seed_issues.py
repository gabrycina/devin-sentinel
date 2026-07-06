"""Create one GitHub issue per curated finding on the target fork.

These issues are the observable *input* to the pipeline. Labeling one with the
trigger label (locally, or via the real webhook) hands it to Devin.

Usage:  python scripts/seed_issues.py [--label]
  --label   also apply the trigger label immediately (fires the webhook if a
            real GitHub webhook is configured; otherwise just tags the issue).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import github_client, scanner  # noqa: E402
from app.config import settings  # noqa: E402
from app.issue_format import to_issue_body  # noqa: E402


def main() -> None:
    apply_label = "--label" in sys.argv
    github_client.ensure_label(
        settings.trigger_label, "5319e7", "Hand this finding to Devin for autonomous remediation"
    )
    github_client.ensure_label("security", "d73a4a", "Security finding")

    findings = scanner.load_curated()
    print(f"Seeding {len(findings)} issues into {settings.github_repo}\n")
    for f in findings:
        labels = ["security", f"severity:{f.severity}"]
        if apply_label:
            labels.append(settings.trigger_label)
        github_client.ensure_label(f"severity:{f.severity}", "ededed")
        issue = github_client.create_issue(
            title=f"[{f.severity.upper()}] {f.title}",
            body=to_issue_body(f),
            labels=labels,
        )
        print(f"  #{issue['number']:<4} {f.id}  ->  {issue['url']}")

    print("\nDone. Add the "
          f"'{settings.trigger_label}' label to an issue to dispatch it to Devin,")
    print("or run:  curl -X POST localhost:8000/api/scan")


if __name__ == "__main__":
    main()
