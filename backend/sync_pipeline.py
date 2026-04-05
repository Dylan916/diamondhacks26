"""
sync_pipeline.py — Orchestrates the full sync flow and yields log strings for SSE.
"""

import asyncio
from typing import AsyncGenerator

from .browser_agent import run_agent
from .llm_processor import process_raw_data
from .database import is_duplicate, save_assignment


async def run_sync(canvas_url: str) -> AsyncGenerator[str, None]:
    """
    Async generator that runs the full sync pipeline and yields
    human-readable log strings at each step.

    The FastAPI route streams these as Server-Sent Events.
    """

    # ── Step 1: Launch the Browser Use agent ─────────────────────────────────
    yield "Opening Canvas using your existing Chrome session..."

    try:
        raw_text = await run_agent(canvas_url)
    except Exception as e:
        yield f"❌ Browser agent error: {e}"
        return

    if not raw_text or not raw_text.strip():
        yield "❌ Browser agent returned no data. Make sure Chrome is closed and you are logged into Canvas, then try again."
        return

    yield "✅ Browser agent finished scraping Canvas"
    yield f"📄 Raw data collected ({len(raw_text):,} characters)"

    # ── Step 2: Gemini post-processing ───────────────────────────────────────
    yield "🤖 Sending data to Gemini for classification and date parsing..."

    try:
        assignments = process_raw_data(raw_text)
    except Exception as e:
        yield f"❌ Gemini processing error: {e}"
        return

    if not assignments:
        yield "⚠️  Gemini returned no structured assignments. The page content may be empty or in an unexpected format."
        return

    yield f"✅ Gemini processed {len(assignments)} assignment(s)"

    # ── Step 3: Deduplication + save to SQLite ────────────────────────────────
    yield "💾 Saving assignments..."

    added = 0
    skipped = 0

    for assignment in assignments:
        title = assignment.get("title", "Untitled")
        course = assignment.get("course", "Unknown")
        due_date = assignment.get("due_date")

        try:
            if is_duplicate(title, course, due_date):
                yield f"⏭️  Skipped duplicate: {title} ({course})"
                skipped += 1
                continue

            save_assignment(assignment)
            yield f"✅ Saved: {title} ({course})"
            added += 1

        except Exception as e:
            yield f"⚠️  Failed to save '{title}': {e}"

    # ── Step 4: Done ─────────────────────────────────────────────────────────
    yield (
        f"🎉 Sync complete! {added} assignment(s) saved, "
        f"{skipped} duplicate(s) skipped."
    )
