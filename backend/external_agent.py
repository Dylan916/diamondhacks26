import os
import time
from dotenv import load_dotenv
from pydantic import BaseModel
from browser_use_sdk.v3 import BrowserUse
from datetime import date

EXTERNAL_AGENT_TASK = """
Navigate to {URL}.

Today's date is {TODAY}. Your goal is to extract ALL assignments. 

## MANDATORY ACTION: Go Beyond the Homepage
1. **Find and CLICK** the link for 'Syllabus', 'Schedule', 'Course Calendar', or 'Assignments'.
2. **VERIFY** you have navigated to a different page before you start extracting. 
3. **DO NOT** just scrape the homepage. The homepage usually has an incomplete list. The Syllabus is the source of truth.

## Extraction Rules
- Scrape every lab, project, exam, and assignment listed.
- For recurring items (e.g. "Labs due every Friday"), compute the specific ISO 8601 dates for the rest of the term.
- Specifically look for rows like "Tue Apr 7 | PROJ 1 | Project 1 Checkpoint".

## Classification (Type)
- Lab -> "lab"
- Project, Checkpoint, Prototype, Peer Review -> "project"
- Exam, Midterm, Final -> "exam"
- Quiz -> "quiz"
- Otherwise -> "assignment"

## Output Format
- Due Date MUST be ISO 8601: "2026-04-14T23:59:00". Assume {YEAR} if needed.

Return ONLY the structured JSON.
"""

class Assignment(BaseModel):
    title: str
    course: str
    due_date: str | None = None
    type: str | None = None  # lab, project, exam, quiz, assignment

class AssignmentList(BaseModel):
    assignments: list[Assignment]

def run_external_agent(urls: list[str]) -> tuple[str, str, str]:
    """
    Creates a persistent session on Browser Use Cloud v3 for external sites.
    Returns (task_id, session_id, live_preview_url).
    """
    load_dotenv(override=True)
    api_key = os.getenv("BROWSER_USE_API_KEY")

    if not api_key:
        raise ValueError("BROWSER_USE_API_KEY environment variable is missing!")

    client = BrowserUse(api_key=api_key)
    
    # 1. Create a session 
    session = client.sessions.create(
        keep_alive=True
    )

    # 2. Build task prompt with current date injected so agent can compute dates
    target_url = urls[0] if urls else "https://google.com"
    today = date.today()
    task_prompt = (
        EXTERNAL_AGENT_TASK
        .replace("{URL}", target_url)
        .replace("{TODAY}", today.isoformat())
        .replace("{YEAR}", str(today.year))
    )

    # Switching back to claude-sonnet-4.6 for better reasoning and reliability.
    # bu-ultra was taking too long and missing complex patterns.
    task_resp = client.sessions.create(
        task=task_prompt,
        session_id=session.id,
        model="claude-sonnet-4.6",
        output_schema=AssignmentList.model_json_schema(),
        max_cost_usd=0.05,  # Lowered safety cap to protect credits
    )

    live_url = getattr(session, "live_url", None)
    if not live_url:
         live_url = f"https://cloud.browser-use.com/run/{session.id}"

    return str(task_resp.id), str(session.id), live_url


def poll_external_result(task_id: str) -> str:
    """
    Synchronously polls the task status on the cloud API until completion.
    """
    if not task_id:
        return ""
        
    load_dotenv(override=True)
    client = BrowserUse(api_key=os.getenv("BROWSER_USE_API_KEY"))

    while True:
        task = client.tasks.get_task(task_id=task_id)
        if task.status in ["done", "failed", "stopped"]:
            return str(task.output) if getattr(task, "output", None) else ""
        time.sleep(2)
