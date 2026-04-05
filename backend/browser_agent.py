"""
browser_agent.py — Browser Use agent powered by Gemini Flash.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent

from .prompts import AGENT_TASK

load_dotenv()


async def run_agent(canvas_url: str, username: str, password: str) -> str:
    """
    Launch a Browser Use agent that logs into Canvas and scrapes all
    assignments, syllabus content, and announcement dates.

    Returns one large text blob with all scraped data combined.
    The browser window is NOT headless so the user can complete MFA manually.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )

    task = AGENT_TASK.format(
        canvas_url=canvas_url.rstrip("/"),
        username=username,
        password=password,
    )

    agent = Agent(
        task=task,
        llm=llm,
    )

    result = await agent.run()

    # Browser Use returns an AgentHistoryList; extract text from final result
    if hasattr(result, "final_result"):
        output = result.final_result()
    elif hasattr(result, "__str__"):
        output = str(result)
    else:
        output = repr(result)

    return output or ""
