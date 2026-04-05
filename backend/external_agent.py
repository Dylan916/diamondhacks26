"""
external_agent.py
Launch a Browser Use agent with an ephemeral (clean) browser to scrape external websites.
"""

import os
from dotenv import load_dotenv
from browser_use import Agent, Browser, BrowserProfile

from langchain_google_genai import ChatGoogleGenerativeAI
from .prompts import EXTERNAL_AGENT_TASK
from .canvas_agent import CustomGeminiLLM

load_dotenv()

async def run_external_agent(urls: list[str]) -> str:
    """
    Launch the External scraping agent for a list of URLs.
    Uses a completely clean browser so it can run concurrently with Canvas agent without Chromium profile lock issues.
    Returns raw scraped text blob.
    """
    if not urls:
        return ""

    llm = CustomGeminiLLM(
        model="gemini-2.0-flash-exp",
        google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
    )

    browser_profile = BrowserProfile(
        headless=False,
    )

    browser = Browser(browser_profile=browser_profile)

    formatted_task = EXTERNAL_AGENT_TASK + f"\n\nURLS TO SCRAPE:\n{chr(10).join(urls)}"

    agent = Agent(
        task=formatted_task,
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
