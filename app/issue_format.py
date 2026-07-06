"""Render a Finding into a GitHub issue body and parse it back out.

The issue is both human-readable (for the VP browsing GitHub) and
machine-readable: we embed the finding as JSON inside an HTML comment so the
webhook handler can reconstruct the exact Finding when the issue is labeled,
without any shared database between the seeder and the listener.
"""
from __future__ import annotations

import json
import re

from .config import settings
from .models import Finding

_MARKER = "sentinel-finding"
_RE = re.compile(rf"<!--\s*{_MARKER}:\s*(\{{.*?\}})\s*-->", re.DOTALL)


def to_issue_body(finding: Finding) -> str:
    refs = "\n".join(f"- {r}" for r in finding.references) or "- (n/a)"
    payload = json.dumps(finding.to_dict())
    return f"""\
**Severity:** `{finding.severity.upper()}`  |  **Source:** {finding.source}  |  **CVE:** {finding.cve or 'n/a'}

**Package:** `{finding.package}` (`{finding.ecosystem}`)
**Vulnerable:** `{finding.vulnerable_version}` → **Fixed in:** `{finding.fixed_version or 'latest safe'}`

### Description
{finding.description}

### References
{refs}

---
> Add the **`{settings.trigger_label}`** label to hand this to Devin for autonomous remediation.

<!-- {_MARKER}: {payload} -->
"""


def parse_finding(issue_body: str) -> Finding | None:
    if not issue_body:
        return None
    m = _RE.search(issue_body)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
        return Finding(**data)
    except Exception:
        return None
