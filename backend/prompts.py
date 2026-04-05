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

EXTERNAL_AGENT_TASK = """
Navigate to {URL}.

Today's date is {TODAY}. Your goal is to extract ALL assignments from this course page.

## Step 1: Find the Syllabus
- Look for links or tabs labeled: Syllabus, Schedule, Course Schedule, Calendar, Assignments, or similar.
- CLICK into the Syllabus/Schedule page — do NOT just read the homepage. The homepage rarely has full assignment info.

## Step 2: Extract EVERYTHING
- Look for ANY date mention — weeks, days of the week, specific dates, relative dates.
- If the syllabus says something like "Labs due every Wednesday at 11:59pm", compute the actual dates for all remaining Wednesdays this quarter/semester.
- If it says "Week 3: Project 1 due", estimate the actual date based on the quarter start.
- Look for ALL of these: assignments, labs, projects, checkpoints, peer reviews, exams, quizzes, readings.

## Step 3: Classify each item
Classify each item's type field as one of: "lab", "project", "exam", "quiz", "assignment"
- If title contains Lab → "lab"
- If title contains Project, Checkpoint, or Prototype → "project"  
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
You are a highly analytical AI system instructed to process raw scraped text into a JSON array of student assignments.
You may receive messy text, memory logs, or action descriptions. Your job is to find the assignment titles and dates within that mess.

1. Clean and standardize all dates to ISO 8601 format (e.g. "2024-10-14T23:59:00").
2. Classify each item by type (assignment, exam, project, etc.).
3. Deduplicate items.

YOU MUST RETURN ONLY A RAW JSON ARRAY. NO MARKDOWN. NO EXPLANATIONS.
If you cannot find any assignments in the text, return an empty array: []

Return EXACTLY THIS FORMAT:
[
  {{
    "title": "string",
    "course": "string",
    "due_date": "string (ISO 8601)",
    "type": "string",
    "source": "string",
    "source_url": "string or null",
    "needs_review": boolean
  }}
]
"""
