"""Replay a GitHub `pull_request.opened` webhook to trigger the Govern workload.

Usage:  python scripts/simulate_pr.py <pr_number>
The server fetches the PR's changed files, the policy engine classifies it, and
Devin is dispatched to produce the required governance artifacts.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import github_client  # noqa: E402
from app.config import settings  # noqa: E402

TARGET = "http://localhost:8000/webhooks/github"


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: simulate_pr.py <pr_number>")
    number = int(sys.argv[1])
    pr = github_client.get_pr(number) or {}
    payload = {
        "action": "opened",
        "pull_request": {
            "number": number,
            "title": pr.get("title", f"PR #{number}"),
            "html_url": pr.get("html_url", f"https://github.com/{settings.github_repo}/pull/{number}"),
        },
    }
    raw = json.dumps(payload).encode()
    headers = {"X-GitHub-Event": "pull_request", "Content-Type": "application/json"}
    if settings.github_webhook_secret:
        sig = hmac.new(settings.github_webhook_secret.encode(), raw, hashlib.sha256).hexdigest()
        headers["X-Hub-Signature-256"] = f"sha256={sig}"
    print(f"POST {TARGET}  (PR #{number})")
    print(httpx.post(TARGET, content=raw, headers=headers, timeout=30).text)


if __name__ == "__main__":
    main()
