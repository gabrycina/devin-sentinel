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

# We force every session to emit a schema. Reading this off the finished session
# is what lets the dashboard show authoritative outcomes instead of guessing from
# free-text. Each workload gets a schema shaped to its deliverables.
_SECURITY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "outcome": {"type": "string", "enum": ["fixed", "partial", "failed", "not_applicable"]},
        "pr_url": {"type": "string"},
        "tests_passed": {"type": "boolean"},
        "summary": {"type": "string"},
        "files_changed": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["outcome", "summary"],
}

_GOVERNANCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "outcome": {"type": "string", "enum": ["complete", "partial", "failed"]},
        "artifacts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "path": {"type": "string"},
                    "needs_human_approval": {"type": "boolean"},
                },
            },
            "description": "Each governance artifact produced (threat model, rollback plan, ADR, etc.).",
        },
        "unmet_requirements": {"type": "array", "items": {"type": "string"}},
        "review_comment_posted": {"type": "boolean"},
        "summary": {"type": "string"},
    },
    "required": ["outcome", "summary"],
}

_INCIDENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "outcome": {"type": "string", "enum": ["mitigated", "resolved", "investigating", "failed"]},
        "suspect_commit": {"type": "string", "description": "The commit identified as the likely cause."},
        "root_cause": {"type": "string"},
        "rca_issue_url": {"type": "string"},
        "rollback_pr_url": {"type": "string"},
        "slack_notified": {"type": "boolean"},
        "summary": {"type": "string"},
    },
    "required": ["outcome", "summary"],
}

_SCHEMAS = {
    "security": _SECURITY_SCHEMA,
    "governance": _GOVERNANCE_SCHEMA,
    "incident": _INCIDENT_SCHEMA,
}


def schema_for(workload: str) -> dict[str, Any]:
    return _SCHEMAS.get(workload, _SECURITY_SCHEMA)


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
        workload: str = "security",
        idempotent: bool = True,
    ) -> dict[str, Any]:
        """Launch a Devin session. Returns {session_id, url, is_new_session}."""
        body: dict[str, Any] = {
            "prompt": prompt,
            "idempotent": idempotent,
            "max_acu_limit": settings.max_acu_per_session,
            "structured_output_schema": schema_for(workload),
            "tags": [settings.fleet_tag, workload, *(tags or [])],
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
