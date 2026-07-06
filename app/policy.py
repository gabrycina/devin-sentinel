"""The rules engine: classify a change and determine required engineering artifacts.

Encodes an enterprise's change-management policy (policy.yaml) as code. The policy
is mutable at runtime: the Rules-engine UI can edit tiers, required artifacts, and
human-approval flags, and those edits take effect immediately for new pull requests.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .models import PolicyStatus

POLICY_FILE = Path(__file__).resolve().parent.parent / "policy.yaml"

# In-memory working copy of the policy (seeded from disk, editable at runtime).
_state: dict[str, Any] = {"policy": None}


def _load_from_disk() -> dict[str, Any]:
    return yaml.safe_load(POLICY_FILE.read_text())


def get_policy() -> dict[str, Any]:
    if _state["policy"] is None:
        _state["policy"] = _load_from_disk()
    return _state["policy"]


def set_policy(new: dict[str, Any]) -> dict[str, Any]:
    """Replace the active policy and persist it to policy.yaml."""
    if not isinstance(new, dict) or "tiers" not in new:
        raise ValueError("policy must be an object with a 'tiers' list")
    new.setdefault("human_approval_required", [])
    new.setdefault("artifacts", get_policy().get("artifacts", {}))
    _state["policy"] = new
    try:
        POLICY_FILE.write_text(yaml.safe_dump(new, sort_keys=False))
    except Exception:
        pass  # persistence is best-effort (read-only FS in some containers)
    return new


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    out, i = "", 0
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
    """Return the governance requirements for a set of changed files."""
    policy = get_policy()
    approval = set(policy.get("human_approval_required", []))
    descriptions = policy.get("artifacts", {})

    chosen = None
    matched_paths: list[str] = []
    for tier in policy["tiers"]:
        hits = [p for p in changed_paths if _matches(p, tier.get("match_paths", []))]
        if hits:
            chosen = tier
            matched_paths = hits
            break
    if chosen is None:
        chosen = policy["tiers"][-1]

    policies = []
    for art in chosen.get("require", []):
        policies.append(
            {
                "name": art,
                "description": descriptions.get(art, art),
                "status": PolicyStatus.PENDING.value,
                "needs_human_approval": art in approval,
            }
        )

    return {
        "tier": chosen["name"],
        "tier_description": chosen.get("description", ""),
        "matched_paths": matched_paths[:8],
        "required_artifacts": chosen.get("require", []),
        "policies": policies,
        "descriptions": descriptions,
    }
