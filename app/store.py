"""SQLite persistence for control-plane jobs. Dependency-free.

One row per job, idempotent on `job_id` so replaying an event or re-running a
scan never creates duplicate work. `policies` and `details` are stored as JSON.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from typing import Any

from .config import settings
from .models import OPEN_STATUSES, Job

_lock = threading.Lock()

# Columns that hold JSON-encoded structures.
_JSON_COLS = {"policies", "details"}

_COLUMNS = [
    "job_id", "workload", "event_type", "severity", "title", "reason", "source",
    "repo", "issue_number", "issue_url", "session_id", "session_url",
    "devin_status", "devin_status_detail", "acus_consumed", "status", "pr_url",
    "tests_passed", "summary", "error", "policies", "details", "eng_minutes_saved",
    "created_at", "dispatched_at", "completed_at",
]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS events (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        REAL,
    kind      TEXT,
    job_id    TEXT,
    message   TEXT
);
"""

# Column -> SQLite type, used to lazily migrate the jobs table.
_COL_TYPES = {
    "workload": "TEXT", "event_type": "TEXT", "severity": "TEXT", "title": "TEXT",
    "reason": "TEXT", "source": "TEXT", "repo": "TEXT", "issue_number": "INTEGER",
    "issue_url": "TEXT", "session_id": "TEXT", "session_url": "TEXT",
    "devin_status": "TEXT", "devin_status_detail": "TEXT", "acus_consumed": "REAL",
    "status": "TEXT", "pr_url": "TEXT", "tests_passed": "INTEGER", "summary": "TEXT",
    "error": "TEXT", "policies": "TEXT", "details": "TEXT",
    "eng_minutes_saved": "REAL", "created_at": "REAL", "dispatched_at": "REAL",
    "completed_at": "REAL",
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _lock, _connect() as conn:
        conn.executescript(_SCHEMA)
        existing = {r["name"] for r in conn.execute("PRAGMA table_info(jobs)")}
        for col, typ in _COL_TYPES.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE jobs ADD COLUMN {col} {typ}")


def _row_to_job(row: sqlite3.Row) -> Job:
    d = dict(row)
    for col in _JSON_COLS:
        d[col] = json.loads(d[col]) if d.get(col) else ([] if col == "policies" else {})
    if d.get("tests_passed") is not None:
        d["tests_passed"] = bool(d["tests_passed"])
    return Job(**{k: d.get(k) for k in _COLUMNS})


def upsert(job: Job) -> None:
    d = job.to_dict()
    for col in _JSON_COLS:
        d[col] = json.dumps(d.get(col) or ([] if col == "policies" else {}))
    if d.get("tests_passed") is not None:
        d["tests_passed"] = int(d["tests_passed"])
    placeholders = ", ".join(f":{c}" for c in _COLUMNS)
    updates = ", ".join(f"{c}=excluded.{c}" for c in _COLUMNS if c != "job_id")
    sql = (
        f"INSERT INTO jobs ({', '.join(_COLUMNS)}) VALUES ({placeholders}) "
        f"ON CONFLICT(job_id) DO UPDATE SET {updates}"
    )
    with _lock, _connect() as conn:
        conn.execute(sql, {c: d.get(c) for c in _COLUMNS})


def get(job_id: str) -> Job | None:
    with _lock, _connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    return _row_to_job(row) if row else None


def all_jobs() -> list[Job]:
    with _lock, _connect() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    return [_row_to_job(r) for r in rows]


def open_jobs() -> list[Job]:
    marks = ",".join("?" * len(OPEN_STATUSES))
    with _lock, _connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM jobs WHERE status IN ({marks}) AND session_id != ''",
            OPEN_STATUSES,
        ).fetchall()
    return [_row_to_job(r) for r in rows]


def log_event(kind: str, job_id: str = "", message: str = "") -> None:
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO events (ts, kind, job_id, message) VALUES (?, ?, ?, ?)",
            (time.time(), kind, job_id, message),
        )


def recent_events(limit: int = 40) -> list[dict[str, Any]]:
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
