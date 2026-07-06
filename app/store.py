"""SQLite persistence for remediations. Deliberately dependency-free.

One row per finding. The pipeline is idempotent on `finding_id` so re-running a
scan or replaying a webhook never creates duplicate work.
"""
from __future__ import annotations

import sqlite3
import threading
import time
from typing import Any

from .config import settings
from .models import OPEN_STATUSES, Remediation, Status

_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS remediations (
    finding_id           TEXT PRIMARY KEY,
    source               TEXT,
    severity             TEXT,
    title                TEXT,
    package              TEXT,
    cve                  TEXT,
    status               TEXT,
    issue_number         INTEGER,
    issue_url            TEXT,
    session_id           TEXT,
    session_url          TEXT,
    devin_status         TEXT,
    devin_status_detail  TEXT,
    acus_consumed        REAL,
    pr_url               TEXT,
    tests_passed         INTEGER,
    summary              TEXT,
    error                TEXT,
    created_at           REAL,
    dispatched_at        REAL,
    completed_at         REAL
);
CREATE TABLE IF NOT EXISTS events (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        REAL,
    kind      TEXT,
    finding_id TEXT,
    message   TEXT
);
"""

_COLUMNS = [
    "finding_id", "source", "severity", "title", "package", "cve", "status",
    "issue_number", "issue_url", "session_id", "session_url", "devin_status",
    "devin_status_detail", "acus_consumed", "pr_url", "tests_passed", "summary",
    "error", "created_at", "dispatched_at", "completed_at",
]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _lock, _connect() as conn:
        conn.executescript(_SCHEMA)


def _row_to_remediation(row: sqlite3.Row) -> Remediation:
    d = dict(row)
    if d.get("tests_passed") is not None:
        d["tests_passed"] = bool(d["tests_passed"])
    return Remediation(**d)


def upsert(rem: Remediation) -> None:
    d = rem.to_dict()
    if d.get("tests_passed") is not None:
        d["tests_passed"] = int(d["tests_passed"])
    placeholders = ", ".join(f":{c}" for c in _COLUMNS)
    updates = ", ".join(f"{c}=excluded.{c}" for c in _COLUMNS if c != "finding_id")
    sql = (
        f"INSERT INTO remediations ({', '.join(_COLUMNS)}) VALUES ({placeholders}) "
        f"ON CONFLICT(finding_id) DO UPDATE SET {updates}"
    )
    with _lock, _connect() as conn:
        conn.execute(sql, {c: d.get(c) for c in _COLUMNS})


def get(finding_id: str) -> Remediation | None:
    with _lock, _connect() as conn:
        row = conn.execute(
            "SELECT * FROM remediations WHERE finding_id = ?", (finding_id,)
        ).fetchone()
    return _row_to_remediation(row) if row else None


def all_remediations() -> list[Remediation]:
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM remediations ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_remediation(r) for r in rows]


def open_remediations() -> list[Remediation]:
    """Rows the poller still needs to reconcile against Devin."""
    marks = ",".join("?" * len(OPEN_STATUSES))
    with _lock, _connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM remediations WHERE status IN ({marks}) AND session_id != ''",
            OPEN_STATUSES,
        ).fetchall()
    return [_row_to_remediation(r) for r in rows]


def log_event(kind: str, finding_id: str = "", message: str = "") -> None:
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO events (ts, kind, finding_id, message) VALUES (?, ?, ?, ?)",
            (time.time(), kind, finding_id, message),
        )


def recent_events(limit: int = 40) -> list[dict[str, Any]]:
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
