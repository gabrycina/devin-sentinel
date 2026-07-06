"""The rules engine: classify a change and determine required engineering artifacts.

This is what turns a raw `pull_request.opened` event into a governed job — it
encodes an enterprise's change-management policy (policy.yaml) as code.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .models import PolicyStatus

POLICY_FILE = Path(__file__).resolve().parent.parent / "policy.yaml"


@lru_cache(maxsize=1)
def load_policy() -> dict[str, Any]:
    return yaml.safe_load(POLICY_FILE.read_text())


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    # Translate a path glob (supporting **) into a regex.
    out = ""
    i = 0
    while i < len(pattern):
        if pattern[i : i + 2] == "**":
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile("^" + out + "$")


def _matches(path: str, patterns: list[str]) -> bool:
    return any(_glob_to_regex(p).search(path) for p in patterns)


def classify(changed_paths: list[str]) -> dict[str, Any]:
    """Return the governance requirements for a set of changed files.

    Picks the highest-priority tier (tiers are listed most-critical first) that
    matches any changed path, and expands it into concrete policy requirements.
    """
    policy = load_policy()
    approval = set(policy.get("human_approval_required", []))
    descriptions = policy.get("artifacts", {})

    chosen = None
    matched_paths: list[str] = []
    for tier in policy["tiers"]:
        hits = [p for p in changed_paths if _matches(p, tier["match_paths"])]
        if hits:
            chosen = tier
            matched_paths = hits
            break
    if chosen is None:
        chosen = policy["tiers"][-1]  # fall back to the least strict tier

    policies = []
    for art in chosen["require"]:
        needs_approval = art in approval
        policies.append(
            {
                "name": art,
                "description": descriptions.get(art, art),
                # produced-vs-pending is resolved later from Devin's output;
                # here we only encode whether a human must ultimately approve it.
                "status": PolicyStatus.PENDING.value,
                "needs_human_approval": needs_approval,
            }
        )

    return {
        "tier": chosen["name"],
        "tier_description": chosen["description"],
        "matched_paths": matched_paths[:8],
        "required_artifacts": chosen["require"],
        "policies": policies,
        "descriptions": descriptions,
    }
