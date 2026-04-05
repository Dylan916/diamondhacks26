import os
import time
from dotenv import load_dotenv
from pydantic import BaseModel
from browser_use_sdk.v3 import BrowserUse
from datetime import date

from .prompts import EXTERNAL_RAW_EXTRACT_TASK

class RawExtraction(BaseModel):
    extracted_text: str

def start_external_session(url: str) -> tuple[str, str, str]:
    """
    Creates a persistent session on Browser Use Cloud v3 for raw text extraction for a single URL.
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

    # 2. Build task prompt — simplified for raw text grab
    today = date.today()
    task_prompt = (
        EXTERNAL_RAW_EXTRACT_TASK
        .replace("{URL}", url)
        .replace("{TODAY}", today.isoformat())
    )

    # Dispatch for RAW EXTRACTION
    task_resp = client.sessions.create(
        task=task_prompt,
        session_id=session.id,
        model="claude-sonnet-4.6",
        output_schema=RawExtraction.model_json_schema(),
        max_cost_usd=0.05, 
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
