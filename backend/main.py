"""
main.py — FastAPI app: SSE sync endpoint, assignments endpoint, health check.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel

from .database import init_db, get_all_assignments, clear_db
from .sync_pipeline import run_sync

class SyncRequest(BaseModel):
    external_urls: list[str] = []


app = FastAPI(title="Student Life Autopilot")

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()


# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/assignments")
def get_assignments():
    return get_all_assignments()


@app.post("/api/assignments/reset")
def reset_assignments():
    """Wipe all saved assignments."""
    clear_db()
    return {"status": "success", "message": "Database cleared"}


@app.get("/api/assignments/export/ics")
def export_ics():
    """Generate a .ics calendar file from all saved assignments."""
    assignments = get_all_assignments()

    def _fmt_dt(iso: str) -> str:
        """Convert ISO 8601 string to iCal DTSTART/DTEND format (UTC)."""
        try:
            dt = datetime.fromisoformat(iso)
            return dt.strftime("%Y%m%dT%H%M%SZ")
        except Exception:
            # Fall back to today at noon if parsing fails
            return datetime.utcnow().strftime("%Y%m%dT120000Z")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Student Life Autopilot//Canvas Sync//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for a in assignments:
        due = a.get("due_date")
        if not due:
            continue  # skip items with no date — they'd land on day zero

        dtstart = _fmt_dt(due)
        # DTEND = due date + 1 hour
        try:
            dtend = _fmt_dt(
                (datetime.fromisoformat(due) + timedelta(hours=1)).isoformat()
            )
        except Exception:
            dtend = dtstart

        title = a.get("title", "Untitled")
        course = a.get("course", "")
        summary = f"{title} [{course}]" if course else title
        description = f"Type: {a.get('type', '')} | Source: {a.get('source', '')}"
        uid = str(uuid.uuid4())

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"SUMMARY:{summary}",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            f"DESCRIPTION:{description}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    ics_content = "\r\n".join(lines)

    return PlainTextResponse(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": 'attachment; filename="canvas-assignments.ics"'
        },
    )


@app.post("/api/sync")
async def sync(req: SyncRequest):
    """
    Run the full sync pipeline and stream progress as Server-Sent Events.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        async for log_line in run_sync(external_urls=req.external_urls):
            # Escape any newlines inside the message so SSE framing stays intact
            safe_line = log_line.replace("\n", " ")
            yield f"data: {safe_line}\n\n"

        # Signal the frontend that the stream is finished
        yield "data: __DONE__\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering if proxied
        },
    )
