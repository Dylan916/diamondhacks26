import os
import time
from dotenv import load_dotenv, set_key
from pydantic import BaseModel
from browser_use_sdk.v3 import BrowserUse
from datetime import date

from .prompts import CANVAS_AGENT_TASK

class Assignment(BaseModel):
    title: str
    course: str
    due_date: str | None = None
    type: str | None = None  # lab, project, exam, quiz, assignment

class AssignmentList(BaseModel):
    assignments: list[Assignment]

load_dotenv()

def get_or_create_profile(client: BrowserUse) -> str:
    """
    Checks .env for BROWSER_USE_PROFILE_ID.
    If missing, creates a new cloud profile and saves it to .env.
    """
    profile_id = os.getenv("BROWSER_USE_PROFILE_ID")
    if profile_id:
        return profile_id
    
    print("Creating new Browser Use Cloud Profile...")
    profile = client.profiles.create_profile(name="StudentLifeAutopilot")
    
    # Save it to the .env file locally so we reuse it
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    set_key(env_path, "BROWSER_USE_PROFILE_ID", profile.id)
    os.environ["BROWSER_USE_PROFILE_ID"] = profile.id
    
    return profile.id


def run_canvas_agent() -> tuple[str, str, str]:
    """
    Creates a persistent session on Browser Use Cloud v3.
    Returns (task_id, session_id, live_preview_url).
    """
    load_dotenv(override=True)
    canvas_url = os.getenv("CANVAS_URL", "https://canvas.instructure.com")
    api_key = os.getenv("BROWSER_USE_API_KEY")

    if not api_key:
        raise ValueError("BROWSER_USE_API_KEY environment variable is missing!")

    # v3 client initialization
    client = BrowserUse(api_key=api_key)
    
    # 1. Ensure we have a persistent profile
    profile_id = get_or_create_profile(client)
    
    # 2. Start the session/task
    today = date.today()
    task_prompt = (
        CANVAS_AGENT_TASK
        .replace("{CANVAS_URL}", canvas_url)
        .replace("{TODAY}", today.isoformat())
        .replace("{YEAR}", str(today.year))
    )
    
    # In v3, we can kick off a task immediately in one call or create a session first.
    # To get the live_url immediately, we create the session first.
    session = client.sessions.create(
        profile_id=profile_id,
        keep_alive=True
    )
    
    # Switching to claude-sonnet-4.6 and increasing cap for reliability.
    task_resp = client.sessions.create(
        task=task_prompt,
        session_id=session.id,
        model="claude-sonnet-4.6",
        output_schema=AssignmentList.model_json_schema(),
        max_cost_usd=0.20,  # Lowered safety cap to protect credits
    )

    live_url = getattr(session, "live_url", None)
    if not live_url:
         live_url = f"https://cloud.browser-use.com/run/{session.id}"

    return str(task_resp.id), str(session.id), live_url


def poll_task_result(session_id: str) -> str:
    """
    Polls the session status on v3 API until terminal status detected.
    Relies on v3 BuAgentSessionStatus.
    """
    load_dotenv(override=True)
    from browser_use_sdk.v3 import BrowserUse
    client = BrowserUse(api_key=os.getenv("BROWSER_USE_API_KEY"))

    # Terminal statuses in v3 are idle, stopped, error, timed_out
    terminal_statuses = ["idle", "stopped", "error", "timed_out"]

    while True:
        session = client.sessions.get(session_id=session_id)
        if session.status.value in terminal_statuses:
             # The result is already in structured format!
             # We return it as a string for the downstream JSON processor, 
             # but soon we'll skip the gemini parser entirely.
             return str(session.output) if session.output else ""
        time.sleep(3)