"""
llm_processor.py — Use Gemini Flash to clean and classify raw scraped data.
"""

import os
import json
import re
from datetime import date
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types as genai_types

from .prompts import LLM_SYSTEM_PROMPT

load_dotenv()



def process_raw_data(raw_text: str) -> list[dict]:
    """
    Send the raw scraped blob to Gemini and parse the returned JSON array.
    Falls back to an empty list if parsing fails.
    """
    today = date.today().isoformat()
    system_prompt = LLM_SYSTEM_PROMPT.format(today=today)
    full_prompt = f"{system_prompt}\n\n=== RAW SCRAPED DATA ===\n{raw_text}"

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=full_prompt,
        )
        raw_response = response.text.strip()

        # Strip any accidental markdown fences Gemini might add
        raw_response = _strip_fences(raw_response)

        assignments = json.loads(raw_response)

        if not isinstance(assignments, list):
            print("[llm_processor] Warning: Gemini did not return a list. Got:", type(assignments))
            return []

        # Validate and sanitise each item
        return [_sanitise(a) for a in assignments if isinstance(a, dict)]

    except json.JSONDecodeError as e:
        print(f"[llm_processor] JSON parse error: {e}")
        print(f"[llm_processor] Raw response was:\n{raw_response[:500]}")
        return []
    except Exception as e:
        print(f"[llm_processor] Unexpected error: {e}")
        return []


def _strip_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers if present."""
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    return text.strip()


_VALID_TYPES = {"assignment", "exam", "midterm", "final", "project", "reading", "other"}
_VALID_SOURCES = {"Assignments", "Syllabus", "Announcement", "External Site"}


def _sanitise(item: dict) -> dict:
    """Ensure every required field is present and has a sensible value."""
    return {
        "title":        str(item.get("title") or "Untitled"),
        "course":       str(item.get("course") or "Unknown Course"),
        "due_date":     item.get("due_date") or None,
        "type":         item.get("type") if item.get("type") in _VALID_TYPES else "other",
        "source":       item.get("source") if item.get("source") in _VALID_SOURCES else "Assignments",
        "external_url": item.get("external_url") or None,
        "needs_review": bool(item.get("needs_review", False)),
    }
