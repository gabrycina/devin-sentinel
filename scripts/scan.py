"""Live scan trigger: query OSV.dev against the fork's real requirements and
dispatch a Devin session for every vulnerability found.

This demonstrates the fully autonomous loop (no pre-seeded findings file):
  fetch requirements -> OSV scan -> ingest -> dispatch.

Usage:  python scripts/scan.py [--dispatch]
  (without --dispatch it only prints what it found)
"""
from __future__ import annotations

import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import orchestrator, scanner, store  # noqa: E402
from app.config import settings  # noqa: E402

RAW = f"https://raw.githubusercontent.com/{settings.github_repo}/{settings.github_base_branch}"
SOURCES = [
    (f"{RAW}/requirements/base.txt", "PyPI"),
    (f"{RAW}/requirements/development.txt", "PyPI"),
]


def main() -> None:
    store.init_db()
    do_dispatch = "--dispatch" in sys.argv
    all_findings = []
    for url, eco in SOURCES:
        try:
            text = httpx.get(url, timeout=30).text
        except Exception as e:
            print(f"skip {url}: {e}")
            continue
        found = scanner.run_osv_scan(text, ecosystem=eco)
        print(f"{url.split('/')[-1]}: {len(found)} vulns")
        all_findings.extend(found)

    print(f"\nTotal: {len(all_findings)} findings")
    for f in all_findings:
        print(f"  [{f.severity}] {f.package}=={f.vulnerable_version}  {f.cve}")
        orchestrator.ingest_finding(f)
        if do_dispatch:
            orchestrator.dispatch_security(f)

    if do_dispatch:
        print("\nDispatched all findings to Devin. Watch the dashboard.")
    else:
        print("\n(dry preview — pass --dispatch to launch Devin sessions)")


if __name__ == "__main__":
    main()
