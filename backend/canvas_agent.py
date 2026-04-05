"""
canvas_agent.py
Launch a Browser Use agent using the user's existing Chrome profile to scrape Canvas.
No login required because it uses the persistent OS session.
"""

import os
import platform
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser, BrowserProfile

from .prompts import CANVAS_AGENT_TASK

class CustomGeminiLLM(ChatGoogleGenerativeAI):
    model_config = {**ChatGoogleGenerativeAI.model_config, 'extra': 'allow'}
    provider: str = 'google'

    @property
    def model_name(self) -> str:
        return getattr(self, "model", "gemini-2.0-flash-exp")

load_dotenv()


def _get_chrome_profile_path() -> str:
    """Return the default Chrome user-data-dir for the current OS."""
    system = platform.system()
    if system == "Darwin":  # macOS
        return os.path.expanduser("~/Library/Application Support/Google/Chrome")
    elif system == "Windows":
        return os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    else:  # Linux
        return os.path.expanduser("~/.config/google-chrome")


async def run_canvas_agent() -> str:
    """
    Launch the Canvas scraping agent.
    The browser window runs with `headless=False` so MFA/errors are visible if needed.
    Returns raw scraped text blob.
    """
    # Always reload the dotenv file purely in case the user edits it without restarting Uvicorn
    load_dotenv(override=True)
    canvas_url = os.getenv("CANVAS_URL", "https://canvas.instructure.com")
    
    profile_path = _get_chrome_profile_path()

    llm = CustomGeminiLLM(
        model="gemini-2.0-flash-exp",
        google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
    )

    browser_profile = BrowserProfile(
        headless=False,
        user_data_dir=profile_path,
        profile_directory="Default"
    )
    
    browser = Browser(browser_profile=browser_profile)

    # Inject the URL into the task template dynamically
    task_prompt = CANVAS_AGENT_TASK.replace("{CANVAS_URL}", canvas_url)

    agent = Agent(
        task=task_prompt,
        llm=llm,
        browser=browser,
    )

    result = await agent.run()

    if hasattr(result, "final_result"):
        output = result.final_result()
    elif hasattr(result, "__str__"):
        output = str(result)
    else:
        output = repr(result)

    return output or ""
whe