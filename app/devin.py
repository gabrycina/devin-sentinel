"""Thin, typed client for the Devin v3 Organization API.

Endpoints verified live against https://api.devin.ai/v3:
  POST /v3/organizations/{org}/sessions
  GET  /v3/organizations/{org}/sessions/{session_id}
  GET  /v3/organizations/{org}/sessions
  POST /v3/organizations/{org}/sessions/{session_id}/messages
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import settings

log = logging.getLogger("sentinel.devin")

# Schema we force every remediation session to emit. Reading this off the
# finished session is what lets the dashboard show authoritative outcomes
# instead of guessing from free-text.
REMEDIATION_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "outcome": {
            "type": "string",
            "enum": ["fixed", "partial", "failed", "not_applicable"],
            "description": "Final result of the remediation attempt.",
        },
        "pr_url": {"type": "string", "description": "URL of the opened pull request, if any."},
        "tests_passed": {"type": "boolean", "description": "Whether the relevant test suite passed."},
        "summary": {"type": "string", "description": "One-paragraph summary of what changed and why."},
        "files_changed": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["outcome", "summary"],
}


class DevinClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {settings.devin_api_key}",
                "Content-Type": "application/json",
            },
        )

    # -- writes ----------------------------------------------------------------
    def create_session(
        self,
        prompt: str,
        *,
        title: str | None = None,
        tags: list[str] | None = None,
        idempotent: bool = True,
    ) -> dict[str, Any]:
        """Launch a Devin session. Returns {session_id, url, is_new_session}."""
        body: dict[str, Any] = {
            "prompt": prompt,
            "idempotent": idempotent,
            "max_acu_limit": settings.max_acu_per_session,
            "structured_output_schema": REMEDIATION_OUTPUT_SCHEMA,
            "tags": [settings.fleet_tag, *(tags or [])],
        }
        if title:
            body["title"] = title
        resp = self._client.post(settings.sessions_url, json=body)
        resp.raise_for_status()
        data = resp.json()
        log.info("created devin session %s (%s)", data.get("session_id"), data.get("url"))
        return data

    def send_message(self, session_id: str, message: str) -> None:
        resp = self._client.post(
            f"{settings.session_url(session_id)}/messages", json={"message": message}
        )
        resp.raise_for_status()

    # -- reads -----------------------------------------------------------------
    def get_session(self, session_id: str) -> dict[str, Any]:
        resp = self._client.get(settings.session_url(session_id))
        resp.raise_for_status()
        return resp.json()

    def list_sessions(self, tag: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if tag:
            params["tags"] = tag
        resp = self._client.get(settings.sessions_url, params=params)
        resp.raise_for_status()
        return resp.json().get("items", [])

    def close(self) -> None:
        self._client.close()
