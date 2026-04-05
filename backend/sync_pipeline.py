"""
sync_pipeline.py — Orchestrates the full sync flow and yields log strings for SSE.
"""

import asyncio
from typing import AsyncGenerator

from .canvas_agent import run_canvas_agent
from .external_agent import run_external_agent
from .llm_processor import process_raw_data
from .database import is_duplicate, save_assignment


async def run_sync(external_urls: list[str]) -> AsyncGenerator[str, None]:
    """
    Async generator that runs the full sync pipeline and yields
    human-readable log strings at each step via Server-Sent Events.
    """

    yield "Starting multi-track sync process..."

    # ── Step 1 & 2: Launch Agents in Parallel ────────────────────────────────
    yield "Starting Canvas scrape..."
    if external_urls:
        yield f"Scraping {len(external_urls)} external sites..."
    else:
        yield "No external sites provided. Skipping Track B."

    canvas_task = asyncio.create_task(run_canvas_agent())
    
    external_task = None
    if external_urls:
         external_task = asyncio.create_task(run_external_agent(external_urls))

    try:
        canvas_text = await canvas_task
        yield "Canvas scrape complete"
    except Exception as e:
        canvas_text = ""
        yield f"❌ Canvas agent error: {e}"

    if external_task:
        try:
            external_text = await external_task
            yield "External sites scrape complete"
        except Exception as e:
            external_text = ""
            yield f"❌ External agent error: {e}"
    else:
        external_text = ""

    if not canvas_text.strip() and not external_text.strip():
        yield "❌ Both agents returned no data. Make sure Chrome is closed and your credentials/API keys are correct."
        return

    # ── Step 3: Gemini post-processing ───────────────────────────────────────
    yield "Processing with Gemini..."

    try:
        assignments = process_raw_data(canvas_text, external_text)
    except Exception as e:
        yield f"❌ Gemini processing error: {e}"
        return

    if not assignments:
        yield "⚠️  Gemini returned no structured assignments. The page content may be empty or in an unexpected format."
        return

    yield f"Found {len(assignments)} assignments total"

    # ── Step 4: Deduplication + save to SQLite ────────────────────────────────
    
    added = 0
    skipped = 0

    for assignment in assignments:
        title = assignment.get("title", "Untitled")
        course = assignment.get("course", "Unknown")
        due_date = assignment.get("due_date")

        try:
            if is_duplicate(title, course, due_date):
                skipped += 1
                continue

            save_assignment(assignment)
            yield f"Saved {title} ({course})"
            added += 1

        except Exception as e:
            yield f"⚠️  Failed to save '{title}': {e}"

    # ── Step 5: Done ─────────────────────────────────────────────────────────
    yield f"Sync complete. {added} assignments saved."
