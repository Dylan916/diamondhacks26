"""
System prompts and task instructions for the Student Life Autopilot dual-track scrapers and LLM.
"""

import os

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
