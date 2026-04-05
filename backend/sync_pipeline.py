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

    yield "Starting multi-track sync process..."

    # ── Step 1: Launch Tasks on Browser Use Cloud ───────────────────────
    canvas_session_id = None
    external_session_id = None
    
    external_task_id = None
    external_text = ""
    added = 0
    skipped = 0

    try:
        if external_urls:
            yield f"Initializing External Cloud Agent for {len(external_urls)} sites..."
            try:
                # Returns (task_id, session_id, live_url)
                external_task_id, external_session_id, external_url = await asyncio.to_thread(run_external_agent, external_urls)
                yield f"👉 External Live Viewer: {external_url}"
            except Exception as e:
                yield f"❌ Failed to start External agent: {e}"
                return

        yield "Cloud agent successfully started! Polling status..."

        # Cleanup: Close any orphaned sessions (v3 style)
        try:
            client = BrowserUse()
            sessions_res = client.sessions.list()
            if hasattr(sessions_res, 'sessions'):
                for s in sessions_res.sessions:
                    # Don't kill our own brand-new sessions!
                    if s.status.value == 'running':
                        sid_str = str(s.id)
                        if sid_str != external_session_id and sid_str != canvas_session_id:
                            print(f"Cleaning up orphaned orphan: {sid_str}")
                            client.sessions.stop(s.id)
        except:
            pass 

        # ── Step 2: Polling V3 ──────────────────────────────────────────────
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
            
            yield "Agent is processing your request (V3 Pipeline)..."
            while not external_poll_task.done():
                await asyncio.sleep(5)
                yield "Cloud agent is still working (polling v3 status)..."
            
            # The output is now a dict (AssignmentList schema)
            results_blob = await external_poll_task
            yield "Cloud extraction complete."

        if not results_blob:
            yield "❌ Sync finished but the Cloud returned no results."
            return

        # ── Step 3: Direct Data Processing ──────────────────────────────────
        # results_blob should match AssignmentList: {"assignments": [...]}
        assignments = []
        
        try:
            if hasattr(results_blob, "dict"):
                 # Handle Pydantic model
                 data = results_blob.dict()
                 assignments = data.get("assignments", [])
            elif isinstance(results_blob, dict):
                 # Handle raw dict
                 assignments = results_blob.get("assignments", [])
            elif isinstance(results_blob, str):
                 # Handle stringified JSON
                 try:
                     data = json.loads(results_blob)
                     assignments = data.get("assignments", [])
                 except:
                     yield f"⚠️ Cloud returned raw text instead of JSON: {results_blob[:100]}..."
                     return
            else:
                 yield f"⚠️ Unexpected data type from Cloud: {type(results_blob)}"
                 return
        except Exception as e:
            yield f"⚠️ Data processing error: {e}"
            return

        if not assignments:
            yield "⚠️ No assignments were found on the target pages."
            return

        # ── Step 4: Storage ────────────────────────────────────────────────
        for assignment in assignments:
            title = assignment.get("title", "Untitled")
            course = assignment.get("course", "Unknown")
            # Normalize due date to ISO 8601 for dashboard parsing
            raw_date = assignment.get("due_date")
            due_date = normalize_due_date(raw_date)
            assignment["due_date"] = due_date

            try:
                if is_duplicate(title, course, due_date):
                    skipped += 1
                else:
                    save_assignment(assignment)
                    yield f"Saved: {title} ({course}) — due {due_date or 'TBD'}"
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
