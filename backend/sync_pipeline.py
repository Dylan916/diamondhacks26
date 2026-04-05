"""
sync_pipeline.py — Orchestrates the full sync flow and yields log strings for SSE.
"""

import asyncio
import os
import time
from typing import AsyncGenerator

import json
import re
from datetime import datetime
from .canvas_agent import run_canvas_agent
from .external_agent import run_external_agent
from .database import is_duplicate, save_assignment
from browser_use_sdk.v3 import BrowserUse
from google import genai
from .prompts import LLM_PROCESSING_PROMPT

def refine_with_gemini(raw_text: str, url: str) -> list[dict]:
    """Uses Gemini 1.5 Flash to parse raw syllabus text into structured assignments."""
    if not raw_text:
        raise ValueError("Raw text from browser agent was completely empty.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from environment variables.")

    # Using the modern google-genai client
    client = genai.Client(api_key=api_key)

    now = datetime.now()
    prompt = (
        LLM_PROCESSING_PROMPT
        .replace("{TODAY}", now.date().isoformat())
        .replace("{YEAR}", str(now.year))
        .replace("{URL}", url)
        .replace("{COURSE_NAME}", "DSC 106") # Default for now
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{prompt}\n\nRAW TEXT FROM WEBSITE:\n{raw_text}"
        )
        
        if not response.text:
             raise ValueError("Gemini API replied with an empty text body.")

        # Handle the new response format (which might include markdown)
        text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return data.get("assignments", [])
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from Gemini. Raw Output:\n{response.text}")
    except Exception as e:
         # Propagate the raw API exception upwards
         raise e


def normalize_due_date(raw: str | None) -> str | None:
    """Convert any human-readable date string to ISO 8601. Returns None if unparseable."""
    if not raw:
        return None
    # Already ISO format
    if re.match(r'\d{4}-\d{2}-\d{2}', raw):
        return raw
    try:
        from dateutil import parser as dateutil_parser
        # Strip common noise like 'by', 'at', weekday prefixes
        cleaned = re.sub(r'\bby\b|\bat\b', '', raw, flags=re.IGNORECASE).strip()
        # Default year to current year if not present
        default = datetime(datetime.now().year, 1, 1)
        parsed = dateutil_parser.parse(cleaned, default=default, fuzzy=True)
        return parsed.isoformat()
    except Exception:
        return None  # Drop unparseable dates rather than saving garbage


async def run_sync(external_urls: list[str]) -> AsyncGenerator[str, None]:
    """
    Async generator that runs the full sync pipeline and yields
    human-readable log strings at each step via Server-Sent Events.
    """

    yield "🚀 Starting External Hybrid Sync process..."

    # ── Step 1: Launch Tasks on Browser Use Cloud ───────────────────────
    canvas_session_id = None # Initialize to prevent cleanup error
    external_session_id = None
    external_task_id = None
    added = 0
    skipped = 0

    try:
        # Focusing 100% on External track per user request
        if not external_urls:
             yield "❌ No external URLs provided to sync."
             return

        yield f"Initializing External Cloud Hunter for {len(external_urls)} sites..."
        try:
            # Returns (task_id, session_id, live_url)
            external_task_id, external_session_id, external_url = await asyncio.to_thread(run_external_agent, external_urls)
            yield f"👉 External Live Viewer: {external_url}"
        except Exception as e:
            yield f"❌ Failed to start External agent: {e}"
            return

        yield "Cloud agent successfully started! Hunting for syllabus content..."

        # ── Step 2: Polling V3 (Raw Extraction) ──────────────────────────────
        results_blob = None
        if external_task_id:
            def poll_v3_session(sid):
                client = BrowserUse()
                start_time = time.time()
                # sdk v3 terminal statuses
                terminal_statuses = ["idle", "stopped", "error", "timed_out"]
                
                while True:
                    session = client.sessions.get(sid)
                    if session.status.value in terminal_statuses:
                        return session.output
                    
                    if time.time() - start_time > 300: # 5 min timeout
                        return None
                    time.sleep(5)

            external_poll_task = asyncio.create_task(asyncio.to_thread(poll_v3_session, external_session_id))
            
            while not external_poll_task.done():
                await asyncio.sleep(5)
                yield "Cloud agent is still scanning (polling v3 status)..."
            
            # The output should be a dict: {"extracted_text": "..."}
            results_blob = await external_poll_task
            yield "✅ Cloud extraction complete. Now refining data with AI..."

        if not results_blob:
            yield "❌ Sync finished but the Cloud returned no results."
            return

        # ── Step 3: Hybrid Refinement (The Brain) ────────────────────────────
        raw_text = ""
        if isinstance(results_blob, dict):
             raw_text = results_blob.get("extracted_text", "")
        elif hasattr(results_blob, "extracted_text"):
             raw_text = results_blob.extracted_text

        yield "🧠 Using AI to structure assignments and compute recurring dates..."
        
        try:
            # We pass the first URL as context
            assignments = refine_with_gemini(raw_text, external_urls[0])
            
            if not assignments:
                yield "⚠️ AI completed successfully but returned an empty assignments list. The prompt might be too rigid."
                return
        except Exception as ai_err:
            yield f"⚠️ AI Refinement Failed: {ai_err}"
            return

        yield f"✅ AI successfully refined {len(assignments)} items."

        # ── Step 4: Storage ────────────────────────────────────────────────
        for assignment in assignments:
            title = assignment.get("title", "Untitled")
            course = assignment.get("course", "DSC 106")
            due_date = assignment.get("due_date") # Already standardized by Gemini

            try:
                if is_duplicate(title, course, due_date):
                    skipped += 1
                else:
                    save_assignment(assignment)
                    yield f"Saved: {title} — due {due_date or 'TBD'}"
                    added += 1
            except Exception as e:
                yield f"⚠️ Failed to save {title}: {e}"

        yield f"✅ Sync Complete! {added} added, {skipped} skipped."
        yield "__DONE__"

    except Exception as e:
        yield f"❌ Sync Critical Error: {e}"
    finally:
        # ── Step 5: Resource Cleanup ──────────────────────────────────────
        try:
            client = BrowserUse()
            if external_session_id:
                print(f"Stopping external session {external_session_id}...")
                client.sessions.stop(external_session_id)
            if canvas_session_id:
                print(f"Stopping canvas session {canvas_session_id}...")
                client.sessions.stop(canvas_session_id)
        except:
            pass
