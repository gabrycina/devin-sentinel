"""Replay a GitHub `issues.labeled` webhook against a locally running Sentinel.

Lets you demo the event-driven path without exposing localhost to GitHub. It
builds the exact payload GitHub sends when the trigger label is added to an
issue, signs it if a webhook secret is configured, and POSTs it.

Usage:  python scripts/simulate_event.py [finding_index]
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import scanner  # noqa: E402
from app.config import settings  # noqa: E402
from app.issue_format import to_issue_body  # noqa: E402

TARGET = "http://localhost:8000/webhooks/github"


def main() -> None:
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    finding = scanner.load_curated()[idx]

    payload = {
        "action": "labeled",
        "label": {"name": settings.trigger_label},
        "issue": {
            "number": 9000 + idx,
            "html_url": f"https://github.com/{settings.github_repo}/issues/{9000 + idx}",
            "title": f"[{finding.severity.upper()}] {finding.title}",
            "body": to_issue_body(finding),
            "labels": [{"name": settings.trigger_label}, {"name": "security"}],
        },
    }
    raw = json.dumps(payload).encode()
    headers = {"X-GitHub-Event": "issues", "Content-Type": "application/json"}
    if settings.github_webhook_secret:
        sig = hmac.new(settings.github_webhook_secret.encode(), raw, hashlib.sha256).hexdigest()
        headers["X-Hub-Signature-256"] = f"sha256={sig}"

    print(f"POST {TARGET}  (finding={finding.id})")
    r = httpx.post(TARGET, content=raw, headers=headers, timeout=30)
    print(r.status_code, r.text)


if __name__ == "__main__":
    main()
