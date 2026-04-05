"""
database.py — SQLite setup and queries for assignment caching.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "assignments.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the assignments table if it doesn't already exist, and migrate missing columns."""
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assignments (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                title         TEXT    NOT NULL,
                course        TEXT    NOT NULL,
                due_date      TEXT,
                type          TEXT,
                source        TEXT,
                source_url    TEXT,
                needs_review  INTEGER DEFAULT 0,
                created_at    TEXT    NOT NULL
            )
            """
        )
        # Forward-compatibility: add any missing columns without recreating the table
        existing = {r[1] for r in conn.execute("PRAGMA table_info(assignments)").fetchall()}
        migrations = {
            "source_url": "TEXT",
            "type": "TEXT",
            "source": "TEXT",
            "needs_review": "INTEGER DEFAULT 0",
        }
        for col, col_type in migrations.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE assignments ADD COLUMN {col} {col_type}")
        conn.commit()


def is_duplicate(title: str, course: str, due_date: str | None) -> bool:
    """Return True if an assignment with the same title+course+due_date exists."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM assignments WHERE title = ? AND course = ? AND due_date = ?",
            (title, course, due_date),
        ).fetchone()
    return row is not None


def save_assignment(assignment: dict) -> None:
    """Persist a processed assignment to SQLite."""
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO assignments
                (title, course, due_date, type, source, source_url,
                 needs_review, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assignment.get("title"),
                assignment.get("course"),
                assignment.get("due_date"),
                assignment.get("type"),
                assignment.get("source"),
                assignment.get("source_url"),
                1 if assignment.get("needs_review") else 0,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()


def clear_db() -> None:
    """Wipe the assignments table for a fresh start."""
    with _get_conn() as conn:
        conn.execute("DELETE FROM assignments")
        conn.commit()


def get_all_assignments() -> list[dict]:
    """Return all cached assignments as a list of dicts."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM assignments ORDER BY due_date ASC"
        ).fetchall()
    return [dict(row) for row in rows]
