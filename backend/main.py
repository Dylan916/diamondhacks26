"""
main.py — FastAPI app: SSE sync endpoint, assignments endpoint, health check.
"""

import json
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .database import init_db, get_all_assignments
from .sync_pipeline import run_sync

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


# ── Request models ────────────────────────────────────────────────────────────
class SyncRequest(BaseModel):
    canvas_url: str
    username: str
    password: str


# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/assignments")
def get_assignments():
    return get_all_assignments()


@app.post("/api/sync")
async def sync(body: SyncRequest):
    """
    Run the full sync pipeline and stream progress as Server-Sent Events.
    Each event is formatted as:  data: <message>\n\n
    The stream ends with:        data: __DONE__\n\n
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        async for log_line in run_sync(
            canvas_url=body.canvas_url,
            username=body.username,
            password=body.password,
        ):
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
