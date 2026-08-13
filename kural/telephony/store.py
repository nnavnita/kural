"""SQLite call log.

One row per call, written on call start and updated on call end. Kept as
plain :mod:`sqlite3` (no ORM) since the schema is a single table and the
write volume is one write per call lifecycle event, not per audio frame.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime

_SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
    sid TEXT PRIMARY KEY,
    direction TEXT NOT NULL,
    from_number TEXT,
    to_number TEXT,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT
)
"""


@dataclass(frozen=True)
class CallRecord:
    """One row of the ``calls`` table."""

    sid: str
    direction: str
    from_number: str | None
    to_number: str | None
    status: str
    started_at: str
    ended_at: str | None


def init_db(db_path: str) -> None:
    """Create the ``calls`` table if it doesn't already exist."""
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(_SCHEMA)
        conn.commit()


def record_call_start(
    db_path: str,
    sid: str,
    direction: str,
    from_number: str | None,
    to_number: str | None,
    status: str = "in-progress",
) -> None:
    """Insert a new call row with the current time as ``started_at``."""
    started_at = datetime.now(UTC).isoformat()
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO calls "
            "(sid, direction, from_number, to_number, status, started_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (sid, direction, from_number, to_number, status, started_at),
        )
        conn.commit()


def record_call_end(db_path: str, sid: str, status: str = "completed") -> None:
    """Set ``status`` and ``ended_at`` (current time) on an existing call row."""
    ended_at = datetime.now(UTC).isoformat()
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "UPDATE calls SET status = ?, ended_at = ? WHERE sid = ?",
            (status, ended_at, sid),
        )
        conn.commit()


def get_call(db_path: str, sid: str) -> CallRecord | None:
    """Fetch one call by SID, or ``None`` if it doesn't exist."""
    with closing(sqlite3.connect(db_path)) as conn:
        row = conn.execute(
            "SELECT sid, direction, from_number, to_number, status, started_at, ended_at "
            "FROM calls WHERE sid = ?",
            (sid,),
        ).fetchone()
    return CallRecord(*row) if row else None


def list_calls(db_path: str) -> list[CallRecord]:
    """List all calls, most recently started first."""
    with closing(sqlite3.connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT sid, direction, from_number, to_number, status, started_at, ended_at "
            "FROM calls ORDER BY started_at DESC",
        ).fetchall()
    return [CallRecord(*row) for row in rows]
