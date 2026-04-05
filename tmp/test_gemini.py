import os
import json
from datetime import datetime
from dotenv import load_dotenv
from google import genai

load_dotenv()

RAW_TEXT = """
FULL COURSE SCHEDULE - DSC 106 Spring 2026 Week 1 Mon Mar 30 DISC 1 Disc 1 Wed Apr 1 LEC 1 The Value of Visualization Fri Apr 3 LEC 2 Data & Image Models Fri Apr 3 LAB 1 Lab 1 Week 2 Mon Apr 6 DISC 2 Disc 2 Tue Apr 7 PROJ 1 Project 1 Checkpoint Wed Apr 8 LEC 3 (In)Effective Visual Encoding Fri Apr 10 LEC 4 Perception Fri Apr 10 LAB 2 Lab 2 Week 3 Mon Apr 13 DISC 3 Disc 3 Tue Apr 14 PROJ 1 Project 1: Expository Visualization Wed Apr 15 LEC 5 Color Fri Apr 17 LEC 6 JavaScript
"""

LLM_PROCESSING_PROMPT = """
Extract assignments into JSON. Today is 2026-04-05, Year is 2026.
OUTPUT ONLY JSON.

{
  "assignments": [
    {
      "title": "string",
      "due_date": "ISO8601",
      "type": "lab/project/exam"
    }
  ]
}
"""

def test():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ No API Key found.")
        return

    client = genai.Client(api_key=api_key)
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{LLM_PROCESSING_PROMPT}\n\nTEXT:\n{RAW_TEXT}"
        )
        print("--- RAW RESPONSE ---")
        print(response.text)
        print("--- PARSING TEST ---")
        text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        print(f"Found {len(data.get('assignments', []))} items.")
    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    test()
