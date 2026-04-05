"""
notion_integration.py — Push assignments to a Notion database.
"""

import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

_notion = Client(auth=os.getenv("NOTION_TOKEN"))
_DB_ID = os.getenv("NOTION_DATABASE_ID")


def create_notion_page(assignment: dict) -> str:
    """
    Create a Notion database page for one assignment.
    Returns the new page's ID.
    """
    # Build the properties payload
    properties: dict = {
        "Name": {
            "title": [{"text": {"content": assignment.get("title", "Untitled")}}]
        },
        "Course": {
            "rich_text": [{"text": {"content": assignment.get("course", "")}}]
        },
        "Type": {
            "select": {"name": _normalise_type(assignment.get("type", "other"))}
        },
        "Source": {
            "select": {"name": _normalise_source(assignment.get("source", "Assignments"))}
        },
        "Needs Review": {
            "checkbox": bool(assignment.get("needs_review", False))
        },
    }

    # Due Date is optional — only set if we have a value
    if assignment.get("due_date"):
        properties["Due Date"] = {"date": {"start": assignment["due_date"]}}

    page = _notion.pages.create(
        parent={"database_id": _DB_ID},
        properties=properties,
    )
    return page["id"]


# ── helpers ──────────────────────────────────────────────────────────────────

_TYPE_MAP = {
    "assignment": "Assignment",
    "exam":       "Exam",
    "midterm":    "Midterm",
    "final":      "Final",
    "project":    "Project",
    "reading":    "Reading",
    "other":      "Other",
}

_SOURCE_MAP = {
    "assignments":   "Assignments",
    "syllabus":      "Syllabus",
    "announcement":  "Announcement",
    "external site": "External Site",
}


def _normalise_type(raw: str) -> str:
    return _TYPE_MAP.get(raw.lower().strip(), "Other")


def _normalise_source(raw: str) -> str:
    return _SOURCE_MAP.get(raw.lower().strip(), "Assignments")
