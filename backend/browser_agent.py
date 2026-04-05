"""
browser_agent.py — Browser Use agent powered by Gemini Flash.
Launches using the user's existing Chrome profile — no login required.
"""

import os
import platform
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser
from browser_use import BrowserProfile

from .prompts import AGENT_TASK

load_dotenv()


class CustomGeminiLLM(ChatGoogleGenerativeAI):
    """
    Subclass to bypass Pydantic v2 restrictions that break browser-use telemetry.
    browser-use attempts to set 'ainvoke' and read 'provider', which fails natively
    on the ChatGoogleGenerativeAI object due to extra='forbid'.
    """
    model_config = {**ChatGoogleGenerativeAI.model_config, 'extra': 'allow'}
    provider: str = 'google'

    @property
    def model_name(self) -> str:
        # browser-use token cost service expects this property
        return getattr(self, "model", "gemini-2.0-flash-exp")



def _get_chrome_profile_path() -> str:
    """Return the default Chrome user-data-dir for the current OS."""
    system = platform.system()
    if system == "Darwin":  # macOS
        return os.path.expanduser(
            "~/Library/Application Support/Google/Chrome"
        )
    elif system == "Windows":
        return os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\User Data"
        )
    else:  # Linux / everything else
        return os.path.expanduser("~/.config/google-chrome")


async def run_agent(canvas_url: str) -> str:
    """
    Launch a Browser Use agent using the user's existing Chrome profile.
    Canvas is already logged in — no credentials needed.

    Returns one large text blob with all scraped data combined.
    The browser window is NOT headless so the user can see what's happening.
    """
    profile_path = _get_chrome_profile_path()

    llm = CustomGeminiLLM(
        model="gemini-2.0-flash-exp",
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )

    # Pass the Chrome profile so the existing Canvas session is reused
    browser_profile = BrowserProfile(
        headless=False,
        user_data_dir=profile_path,
        profile_directory="Default",
    )

    browser = Browser(browser_profile=browser_profile)

    task = AGENT_TASK.format(
        canvas_url=canvas_url.rstrip("/"),
        # username/password placeholders are no longer used — kept in template
        # for backwards compatibility but the agent skips the login step
        username="",
        password="",
    )

    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
    )

    result = await agent.run()

    # Browser Use returns an AgentHistoryList; extract text from the final result
    if hasattr(result, "final_result"):
        output = result.final_result()
    elif hasattr(result, "__str__"):
        output = str(result)
    else:
        output = repr(result)

    return output or ""
