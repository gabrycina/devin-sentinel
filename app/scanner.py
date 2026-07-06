"""Scanner layer: turns a repository into a list of Findings.

Two modes:
  * `load_curated()` -- reads findings/superset_findings.json. These were produced
    by querying the OSV.dev advisory database against Superset's actual pinned
    dependencies (requirements/base.txt, requirements/development.txt, and
    superset-frontend/package.json). They are real, verifiable CVEs.
  * `run_osv_scan()` -- re-runs that same OSV query live against a requirements
    file, so the pipeline is not hard-coded to a snapshot. Used by `scripts/scan.py`.

In a production deployment this module is where you would drop in Snyk / Trivy /
Dependabot / CodeQL adapters -- the rest of the pipeline is source-agnostic.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

from .models import Finding

FINDINGS_FILE = Path(__file__).resolve().parent.parent / "findings" / "superset_findings.json"


def load_curated() -> list[Finding]:
    data = json.loads(FINDINGS_FILE.read_text())
    return [Finding(**f) for f in data]


def _severity_from_cvss(vector: str) -> str:
    # Very rough bucket; only used for the live-scan path.
    m = re.search(r"CVSS:3\.[01]/.*", vector or "")
    return "high" if m else "medium"


def run_osv_scan(requirements_text: str, ecosystem: str = "PyPI") -> list[Finding]:
    """Query OSV.dev for every pinned dependency and return one Finding per vuln."""
    pkgs: list[tuple[str, str]] = []
    for line in requirements_text.splitlines():
        m = re.match(r"^([a-zA-Z0-9_.\-]+)==([0-9][^\s;#]*)", line.strip())
        if m:
            pkgs.append((m.group(1), m.group(2)))
    if not pkgs:
        return []

    queries = [{"package": {"ecosystem": ecosystem, "name": n}, "version": v} for n, v in pkgs]
    with httpx.Client(timeout=60) as c:
        results = c.post(
            "https://api.osv.dev/v1/querybatch", json={"queries": queries}
        ).json().get("results", [])

    findings: list[Finding] = []
    label = "pip" if ecosystem == "PyPI" else ecosystem.lower()
    for (name, version), res in zip(pkgs, results):
        for vuln in (res.get("vulns") or []):
            vid = vuln["id"]
            findings.append(
                Finding(
                    id=f"OSV-{name}-{vid}",
                    source=f"osv-scan ({label})",
                    severity="high",
                    title=f"{name} {version} affected by {vid}",
                    description=f"OSV advisory {vid} affects {name}=={version}.",
                    ecosystem=label,
                    package=name,
                    vulnerable_version=version,
                    cve=vid,
                    references=[f"https://osv.dev/vulnerability/{vid}"],
                )
            )
    return findings
