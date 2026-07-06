"""Fire a PagerDuty-style alert into the Respond workload.

Builds the incident payload from the demo service repo's real git history
(so the "recent deploys" are actual commits Devin can bisect), then POSTs it.

Usage:  python scripts/trigger_incident.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402

TARGET = "http://localhost:8000/api/incident"


def _recent_deploys() -> list[dict[str, str]]:
    """Fetch the last few commits of the incident repo via the GitHub API."""
    import json
    url = f"https://api.github.com/repos/{settings.incident_repo}/commits?per_page=5"
    headers = {"Authorization": f"Bearer {settings.github_token}"} if settings.github_token else {}
    commits = httpx.get(url, headers=headers, timeout=30).json()
    return [
        {"sha": c["sha"], "message": c["commit"]["message"].splitlines()[0],
         "deployed_at": c["commit"]["author"]["date"]}
        for c in commits
    ]


def main() -> None:
    incident = {
        "id": f"INC-{time.strftime('%Y%m%d')}-{int(time.time()) % 10000}",
        "service": "checkout-service",
        "severity": "critical",
        "repo": settings.incident_repo,
        "fired_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "error": "5xx spike on /checkout — TypeError: 'NoneType' object is not subscriptable",
        "stacktrace": (
            'File "checkout/api.py", line 8, in handle_checkout\n'
            "    return {\"total\": calculate_total(items, coupon)}\n"
            'File "checkout/pricing.py", line 8, in apply_discount\n'
            "    return round(price * (1 - coupon[\"percent\"] / 100), 2)\n"
            "TypeError: 'NoneType' object is not subscriptable"
        ),
        "grafana": (
            "checkout-service 5xx rate: 0.1% -> 34% at 16:40 UTC. p95 latency flat. "
            "Error budget for the month exhausted. Onset correlates with the 16:30 deploy."
        ),
        "deploys": _recent_deploys(),
    }
    print(f"POST {TARGET}  ({incident['id']} on {incident['service']})")
    print(httpx.post(TARGET, json=incident, timeout=30).text)


if __name__ == "__main__":
    main()
