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
    """Create the assignments table if it doesn't already exist."""
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
                external_url  TEXT,
                needs_review  INTEGER DEFAULT 0,
                notion_page_id TEXT,
                created_at    TEXT    NOT NULL
            )
            """
        )
        conn.commit()


def is_duplicate(title: str, course: str, due_date: str | None) -> bool:
    """Return True if an assignment with the same title+course+due_date exists."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM assignments WHERE title = ? AND course = ? AND due_date = ?",
            (title, course, due_date),
        ).fetchone()
    return row is not None


def save_assignment(assignment: dict, notion_page_id: str) -> None:
    """Persist a processed assignment to SQLite."""
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO assignments
                (title, course, due_date, type, source, external_url,
                 needs_review, notion_page_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assignment.get("title"),
                assignment.get("course"),
                assignment.get("due_date"),
                assignment.get("type"),
                assignment.get("source"),
                assignment.get("external_url"),
                1 if assignment.get("needs_review") else 0,
                notion_page_id,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()


def get_all_assignments() -> list[dict]:
    """Return all cached assignments as a list of dicts."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM assignments ORDER BY due_date ASC"
        ).fetchall()
    return [dict(row) for row in rows]
