"""
llm_processor.py
Combines both raw text blobs from the local agents and calls Gemini post-processing
to extract and map identical JSON structures.
"""

import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

from .prompts import LLM_PROCESSING_PROMPT

load_dotenv()

# Setup GenAI directly
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def process_raw_data(canvas_text: str, external_text: str) -> list[dict]:
    """
    Combines both raw text blobs, calls Gemini, and parses the response into a list of dicts.
    """
    if not canvas_text and not external_text:
        return []

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=LLM_PROCESSING_PROMPT,
    )

    content = f"""
    -- CANVAS RAW TEXT --
    {canvas_text}

    -- EXTERNAL WEBSITES RAW TEXT --
    {external_text}
    """

    try:
        response = model.generate_content(content)
        raw_output = response.text.strip()
        
        # In case the model accidentally includes markdown fences despite instructions
        if raw_output.startswith("```"):
            raw_output = re.sub(r"^```(?:json)?", "", raw_output)
            raw_output = re.sub(r"```$", "", raw_output).strip()

        parsed_data = json.loads(raw_output)
        
        if not isinstance(parsed_data, list):
            parsed_data = [parsed_data]
            
        return parsed_data
    except Exception as e:
        print(f"Error processing LLM output: {e}")
        return []
