"""
System prompts and task instructions for the Student Life Autopilot dual-track scrapers and LLM.
"""

import os

CANVAS_URL = os.environ.get("CANVAS_URL", "https://canvas.instructure.com")

# The canvas agent task template.
# The URL is injected dynamically by the agent at runtime.
# The canvas agent task template.
# The URL is injected dynamically by the agent at runtime.
CANVAS_AGENT_TASK = """
Navigate to {CANVAS_URL}.
If you see a multi-factor authentication (MFA) page, STOP your actions and DO NOT click anything. Wait silently for the user to manually approve the MFA on their phone.

Today's date is {TODAY}. Once you are on the Dashboard:
1. For EVERY course tile you see (e.g. DSC 102, DSC 106, etc.), click into the course.

## Step 1: Scrape the Course Homepage (First Priority)
- Look for a list of upcoming assignments, a calendar, or a schedule table.
- Specifically look for rows like "Tue Apr 7 | PROJ 1 | Project 1 Checkpoint". 
- These are HIGH PRECISION dates. Capture them exactly.

## Step 2: Scrape the Syllabus/Schedule (Deep Dive)
- CLICK into the 'Syllabus' or 'Schedule' page.
- Look for recurring rules (e.g., "Labs due on the following Fridays at 11:59PM").
- Use today's date ({TODAY}) as a reference to compute the dates for these recurring items for the rest of the term.

## Step 3: Classify each item
Classify each item's 'type' field:
- title contains "Lab" -> "lab"
- title contains "Project", "Checkpoint", "Final Project", "Prototype" -> "project"
- title contains "Exam", "Midterm", "Final" -> "exam"
- title contains "Quiz" -> "quiz"
- Otherwise -> "assignment"

## Step 4: Format dates
- Return all dates in ISO 8601 format: "2026-04-14T23:59:00". Assume {YEAR} if missing.

When finished with ALL courses, return the assignments in the requested structured format.
"""

# Simplified Extraction Task (The Muscle)
# This task is intentionally dumb — it just navigates and grabs text.
EXTERNAL_RAW_EXTRACT_TASK = """
Navigate to {URL}.

Today's date is {TODAY}. Your ONLY mission:
1. **Find and CLICK** the link for 'Syllabus', 'Schedule', 'Course Calendar', or 'Assignments'.
2. **VERIFY** the page has changed.
3. **SCROLL** down to ensure all tables/rows are loaded.
4. **GRAB** every single date, assignment name, and schedule row on the page.
5. **DO NOT** worry about formatting. Just return the raw data as a large block of text.

Return EVERYTHING you see related to the course schedule in your `extracted_text` field.
"""

EXTERNAL_AGENT_TASK = """
- If title contains Exam, Midterm, or Final → "exam"
- If title contains Quiz → "quiz"
- Otherwise → "assignment"

## Step 4: Format dates
- Return all dates in ISO 8601 format: "2026-04-14T23:59:00"
- Assume 11:59pm if no time given.
- Assume year {YEAR} if not stated.

Return ONLY the structured data. No explanations.
"""


LLM_PROCESSING_PROMPT = """
Extract assignments into JSON.

Today is {TODAY}, Year is {YEAR}, Course is {COURSE_NAME}.

RULES:
1. Identify dates like "Tue Apr 7" or "Fri Apr 10". 
2. Convert to ISO 8601: "{YEAR}-04-14T23:59:00".
3. Classify: "lab", "project", "exam", "quiz", "assignment".
4. If it says "Labs due every Friday", generate dates for every Friday for 10 weeks from {TODAY}.

OUTPUT ONLY THIS JSON OBJECT:
{{
  "assignments": [
    {{
      "title": "string",
      "course": "{COURSE_NAME}",
      "due_date": "ISO8601",
      "type": "string",
      "source_url": "{URL}"
    }}
  ]
}}
"""
