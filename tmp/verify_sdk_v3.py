import os
import time
from dotenv import load_dotenv
from pydantic import BaseModel
from browser_use_sdk.v3 import BrowserUse

# 1. Define a tiny schema for the test
class TestResult(BaseModel):
    message: str
    status_code: int

def verify_v3():
    load_dotenv()
    api_key = os.getenv("BROWSER_USE_API_KEY")
    if not api_key:
        print("❌ Error: BROWSER_USE_API_KEY not found in .env")
        return

    print(f"🚀 Initializing Browser Use SDK v3.4.0...")
    client = BrowserUse(api_key=api_key)

    try:
        print("🔍 Step 1: Creating a test session with Structured Output...")
        # We use a very simple task to save your credits
        task = "Print the message 'SDK V3 Verification Success' and status_code 200 in JSON format."
        
        # In v3, we can create and run in one go, but we'll use the 'create' flow 
        # to mimic our actual agents.
        session = client.sessions.create(keep_alive=True)
        print(f"✅ Session Created: {session.id}")
        print(f"👉 Live Preview: {getattr(session, 'live_url', 'N/A')}")

        print("⚡ Step 2: Dispatching task with output_schema...")
        run_resp = client.sessions.create(
            task=task,
            session_id=session.id,
            model="bu-mini", # Use the cheapest model for verification
            output_schema=TestResult.model_json_schema()
        )
        print(f"✅ Task Dispatched: {run_resp.id}")

        print("⌛ Step 3: Polling for 'idle' or 'stopped' status...")
        terminal_statuses = ["idle", "stopped", "error", "timed_out"]
        start_time = time.time()
        
        while True:
            # Refresh session to get latest status and output
            s = client.sessions.get(session.id)
            print(f"--- Status: {s.status.value} | Steps: {s.step_count} ---")
            
            if s.status.value in terminal_statuses:
                print(f"🎯 Terminal Status Detected: {s.status.value}")
                print(f"📊 Structured Result: {s.output}")
                
                if s.output and s.output.get("status_code") == 200:
                    print("✅ Verification PASSED: Data extraction is perfect!")
                break
            
            if time.time() - start_time > 60:
                print("❌ Timeout: Verification took too long.")
                break
            time.sleep(3)

    except Exception as e:
        print(f"❌ Verification FAILED: {e}")
    finally:
        print("🧹 Step 4: Testing official client.sessions.stop()...")
        try:
             client.sessions.stop(session.id)
             print("✅ Session Stopped Successfully!")
        except Exception as cleanup_error:
             print(f"⚠️ Cleanup error (might be expected if session already closed): {cleanup_error}")

if __name__ == "__main__":
    verify_v3()
