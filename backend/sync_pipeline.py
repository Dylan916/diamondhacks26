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
from .external_agent import start_external_session
from .database import is_duplicate, save_assignment
from browser_use_sdk.v3 import BrowserUse
from google import genai
from .prompts import LLM_PROCESSING_PROMPT

def refine_with_gemini(raw_text: str, url: str, hint: str = "Unknown Course") -> list[dict]:
    """Uses the specified Gemini model to parse raw syllabus text into structured assignments."""
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
        .replace("{COURSE_NAME}", hint) 
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
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
        return None 


async def process_single_site(url: str, log_queue: asyncio.Queue, session_ids: list[str]):
    """Parallel worker for a single site extraction and refinement."""
    domain = url.split("//")[-1].split("/")[0]
    prefix = f"[{domain}]"
    
    await log_queue.put(f"{prefix} Starting Cloud session...")
    
    try:
        # Launch Agent
        task_id, sid, live_url = await asyncio.to_thread(start_external_session, url)
        session_ids.append(sid)
        await log_queue.put(f"{prefix} 👉 Live Viewer: {live_url}")

        # Polling
        def poll_v3_session(sid):
            client = BrowserUse()
            terminal_statuses = ["idle", "stopped", "error", "timed_out"]
            start_t = time.time()
            while True:
                session = client.sessions.get(sid)
                if session.status.value in terminal_statuses:
                    return session.output
                if time.time() - start_t > 300:
                    return None
                time.sleep(5)

        await log_queue.put(f"{prefix} Agent hunting for schedule content...")
        results_blob = await asyncio.to_thread(poll_v3_session, sid)
        
        if not results_blob:
             await log_queue.put(f"❌ {prefix} Cloud returned no results.")
             return

        # Refinement
        raw_text = ""
        if isinstance(results_blob, dict):
             raw_text = results_blob.get("extracted_text", "")
        elif hasattr(results_blob, "extracted_text"):
             raw_text = results_blob.extracted_text

        await log_queue.put(f"🧠 {prefix} Refining with AI...")
        try:
            # We pass the domain name as a hint for the course title
            assignments = refine_with_gemini(raw_text, url, domain)
        except Exception as ai_err:
            await log_queue.put(f"⚠️ {prefix} AI Error: {ai_err}")
            return

        if not assignments:
            await log_queue.put(f"⚠️ {prefix} AI found 0 assignments.")
            return

        # Storage
        added = 0
        for a in assignments:
            title = a.get("title", "Untitled")
            course = a.get("course", "Course")
            due = a.get("due_date")
            if not is_duplicate(title, course, due):
                save_assignment(a)
                added += 1
        
        await log_queue.put(f"✅ {prefix} Saved {added} new assignments.")

    except Exception as e:
        await log_queue.put(f"❌ {prefix} Critical Error: {e}")


async def run_sync(external_urls: list[str]) -> AsyncGenerator[str, None]:
    """ Orchestrates multiple site syncs in parallel. """

    yield "🚀 Initializing Parallel Multi-Site Sync..."
    
    log_queue = asyncio.Queue()
    session_ids = []
    
    # Launch all workers
    workers = [process_single_site(u, log_queue, session_ids) for u in external_urls]
    gather_task = asyncio.gather(*workers)
    
    # Consume logs until workers are done
    while not (gather_task.done() and log_queue.empty()):
        try:
            # Wait for a log with a timeout so we can check gather_task status
            msg = await asyncio.wait_for(log_queue.get(), timeout=1.0)
            yield msg
        except asyncio.TimeoutError:
            continue

    yield "✅ All sync tracks completed."
    yield "__DONE__"

    # Cleanup
    try:
        client = BrowserUse()
        for sid in session_ids:
            client.sessions.stop(sid)
    except:
        pass
