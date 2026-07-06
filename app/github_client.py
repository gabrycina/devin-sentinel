"""Minimal GitHub REST client (issues + labels + PR state).

Used for two things:
  * seeding the tracking issues that the pipeline remediates, and
  * (optionally) reading PR merge state for the dashboard.

We talk raw REST via httpx so the container needs no `gh` binary.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import settings

log = logging.getLogger("sentinel.github")
_API = "https://api.github.com"


def _client() -> httpx.Client:
    return httpx.Client(
        timeout=30,
        headers={
            "Authorization": f"Bearer {settings.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )


def ensure_label(name: str, color: str = "5319e7", description: str = "") -> None:
    with _client() as c:
        r = c.post(
            f"{_API}/repos/{settings.github_repo}/labels",
            json={"name": name, "color": color, "description": description},
        )
        if r.status_code not in (201, 422):  # 422 = already exists
            r.raise_for_status()


def create_issue(title: str, body: str, labels: list[str]) -> dict[str, Any]:
    with _client() as c:
        r = c.post(
            f"{_API}/repos/{settings.github_repo}/issues",
            json={"title": title, "body": body, "labels": labels},
        )
        r.raise_for_status()
        data = r.json()
    log.info("created issue #%s: %s", data["number"], title)
    return {"number": data["number"], "url": data["html_url"]}


def get_pr(pr_number: int) -> dict[str, Any] | None:
    with _client() as c:
        r = c.get(f"{_API}/repos/{settings.github_repo}/pulls/{pr_number}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
