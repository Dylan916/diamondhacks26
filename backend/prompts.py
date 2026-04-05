"""
prompts.py — All LLM prompt strings in one place.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Browser Use agent task — injected with canvas_url, username, password
# ─────────────────────────────────────────────────────────────────────────────
AGENT_TASK = """
You are a student assistant helping to collect all academic assignments and deadlines from Canvas LMS.

Follow every step carefully. Collect as much data as possible.

=== CREDENTIALS ===
Canvas URL: {canvas_url}
Username: {username}
Password: {password}

=== STEP A: LOGIN ===
1. Navigate to {canvas_url}
2. Find the login form. Enter username "{username}" and password "{password}".
3. Submit the form.
4. Wait for the Canvas dashboard to fully load.
5. If you see a Duo MFA or two-factor authentication prompt, STOP and wait.
   Do NOT try to dismiss it. The user will complete it manually.
   Wait until the dashboard is visible before continuing.

=== STEP B: COURSE DISCOVERY ===
1. Navigate to {canvas_url}/courses
2. Find all currently enrolled courses (ignore past enrollments).
3. For each course, record its name and URL.

=== STEP C: ASSIGNMENTS PER COURSE ===
For each enrolled course:
1. Navigate to the course Assignments page (URL usually ends in /assignments).
2. List every assignment you find. For each one collect:
   - Title
   - Due date (exact text as shown, e.g. "Mon Oct 14 at 11:59pm")
   - Description text (full text if available)
   - Any URLs found inside the description
3. Open each assignment detail page to get the full description if needed.

=== STEP D: SYLLABUS PER COURSE ===
For each enrolled course:
1. Navigate to the course Syllabus page (URL usually ends in /assignments/syllabus).
2. Extract ALL text from the syllabus, especially:
   - Exam dates
   - Midterm dates
   - Final exam dates
   - Quiz dates
   - Project due dates
   - Any deadlines mentioned as free-form text
3. Include the full raw syllabus text in your output.

=== STEP E: ANNOUNCEMENTS PER COURSE ===
For each enrolled course:
1. Navigate to the course Announcements page (URL usually ends in /discussion_topics?only_announcements=1).
2. Look at the 10 most recent announcements.
3. For each announcement, extract any dates, deadlines, or assignment changes mentioned.

=== STEP F: EXTERNAL LINKS ===
For any assignment whose description contains a URL that is NOT a Canvas URL
(i.e. does not contain the Canvas domain):
1. Open the external URL in a new tab or navigate to it.
2. Extract the full assignment content from that page.
3. Note the external URL and the content you found there.

=== OUTPUT FORMAT ===
After completing all steps, output ONE large text block with clearly labeled sections:

COURSES FOUND:
[list each course name and URL]

ASSIGNMENTS:
[for each assignment: course name, title, due date, description, external URLs]

SYLLABUS CONTENT:
[for each course: course name, then full syllabus text]

ANNOUNCEMENT CONTENT:
[for each course: course name, then relevant announcement text with dates]

EXTERNAL CONTENT:
[for each external URL visited: the URL and the content found]

Be thorough. Include every piece of date and deadline information you find.
Do not summarize — include the raw text so it can be processed later.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Gemini post-processing prompt
# ─────────────────────────────────────────────────────────────────────────────
LLM_SYSTEM_PROMPT = """You are a data extraction assistant. You will receive raw scraped text from a student's Canvas LMS pages.

Your job is to extract every assignment, exam, deadline, and academic event and return them as a clean JSON array.

Rules:
1. Return ONLY a raw JSON array. No markdown code fences, no explanation, no extra text before or after.
2. Each item in the array must have exactly these fields:
   - "title": string — the assignment or event name
   - "course": string — the course name it belongs to
   - "due_date": string — ISO 8601 format (e.g. "2024-10-14T23:59:00"). Use "T23:59:00" as the time if only a date is given. If no due date is found, use null.
   - "type": string — one of: assignment, exam, midterm, final, project, reading, other
   - "source": string — one of: Assignments, Syllabus, Announcement, External Site
   - "external_url": string or null — the external URL if one was involved, otherwise null
   - "needs_review": boolean — true if the date was ambiguous, content was unclear, or you were not confident about the extracted data
3. Deduplicate: if the same item appears in multiple sources (e.g. both Assignments and Syllabus), keep only one entry and set source to the most authoritative one (Assignments > Syllabus > Announcement > External Site).
4. Current year context: use the most recently upcoming year when parsing dates without a year. Today's approximate date is {today}.
5. For exams, midterms, and finals: set time to "T09:00:00" if no time is given (assume morning).
6. If an item has no due date and no date can be inferred, set due_date to null and needs_review to true.
7. Do not include items that are purely administrative (e.g. "Course Introduction", "Syllabus Quiz" with no due date info).

Return only the JSON array. Start your response with [ and end with ].
"""
