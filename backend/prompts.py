"""
System prompts and task instructions for the Student Life Autopilot dual-track scrapers and LLM.
"""

import os

CANVAS_URL = os.environ.get("CANVAS_URL", "https://canvas.instructure.com")

# The canvas agent task template.
# The URL is injected dynamically by the agent at runtime.
CANVAS_AGENT_TASK = """
Navigate to {CANVAS_URL}.
If you see a multi-factor authentication (MFA) page, STOP your actions and DO NOT click anything. Wait silently for the user to manually approve the MFA on their phone.
Once you are successfully viewing the Canvas dashboard, locate any list of upcoming assignments, to-dos, or course syllabus schedules.
Extract ALL assignments, quizzes, tests, and readings you can find across all visible active courses.
Once you have found everything, use the 'done' tool to return the completely raw, unformatted text of every assignment title, course, and due date you found.
"""


EXTERNAL_AGENT_TASK = """
You have been given a list of external course websites (e.g. professor sites, department pages, course portals).
Your task is to navigate to EACH url completely one by one.
For each website:
1. Look for and click on links indicating a syllabus page, schedule page, assignments page, or course calendar.
2. Extract every single assignment, deadline, exam, midterm, final, quiz, project, or due date mentioned anywhere on the page or on the linked pages.
3. If you find a link to a PDF syllabus, follow the link and extract the dates from the PDF text/content as well.

Once you are finished, use the 'done' tool to return the completely raw, unformatted text dumping every assignment title, course code/name, and date/deadline string you found.
Include the URL origin for the items if possible.
"""


LLM_PROCESSING_PROMPT = """
You are a highly analytical AI system instructed to unify and process two raw data streams into a single JSON array.
You are receiving scraped text dumps from a student's Canvas instance and from their external course websites.

Your job is to:
1. Clean and standardize all dates to ISO 8601 format (e.g. "2024-10-14T23:59:00"). If no year is provided, assume the current academic year. If no time is provided, assume 23:59:00 local time.
2. Classify each item by type.
3. Deduplicate obvious duplicates (e.g. identical assignment names across Canvas and the external site). If deduplicating, prefer the Canvas source, but combine any extra context.

YOU MUST RETURN ONLY A RAW JSON ARRAY. NO MARKDOWN, NO CODE FENCES, NO EXPLANATIONS.
Return EXACTLY THIS JSON FORMAT (a list of objects):
[
  {{
    "title": "string",
    "course": "string (infer from context if not explicitly labeled)",
    "due_date": "string (ISO 8601)",
    "type": "string (MUST BE EXACTLY ONE OF: assignment, exam, midterm, final, project, reading, quiz, other)",
    "source": "string (MUST BE EXACTLY ONE OF: Canvas Assignments, Canvas Syllabus, Canvas Announcement, External Site)",
    "source_url": "string (the URL it came from, or null if unknown)",
    "needs_review": boolean (true if date was ambiguous, confusing, or could not be confidently parsed)
  }}
]

Output NOTHING ELSE but the `[` starting the array and the `]` ending it.
"""
