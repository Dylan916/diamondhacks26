# Course2Calendar 🎓

A high-speed, AI-powered course schedule sync tool. It uses a cloud-based browser agent to scrape your external course websites and a Gemini AI refiner to extract, classify, and normalize deadlines into a local calendar.

**No API tokens required. Works with any public course syllabus. Free with Gemini Flash.**

---

## Features

- **Cloud Extraction**: Scrapes public syllabus pages using high-speed browser agents.
- **AI Refinement**: Uses Gemini 2.0 Flash to parse messy dates and compute recurring assignments (e.g., "Weekly Labs").
- **Local Database**: Stores assignments in a lightweight SQLite database.
- **Calendar Export**: Download a standard `.ics` file to sync with Apple Calendar, Google Calendar, or Outlook.
- **Privacy First**: No course credentials or passwords are ever stored.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- A Gemini API key from [aistudio.google.com](https://aistudio.google.com)
- A Browser Use Cloud API key from [cloud.browser-use.com](https://cloud.browser-use.com)

---

## 1 — Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Fill in `.env`:
```
GEMINI_API_KEY=your_gemini_key
BROWSER_USE_API_KEY=your_browser_use_cloud_key
```

---

## 2 — Install Backend Dependencies

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

---

## 3 — Install Frontend Dependencies

```bash
cd frontend
npm install
```

---

## 4 — Run the App

**Terminal 1 — Backend:**
```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 5 — Using the App

1. Paste your course website or syllabus URL into the dashboard.
2. Click **Start Sync**.
3. Watch the live activity log as the agent scrapes the schedule.
4. When sync completes, your assignments will appear in the dashboard.
5. Click **Export to Calendar** to download your schedule as an `.ics` file.

---

## Notes

- **Duplicate Detection**: The app automatically skips duplicates matched by title, course, and due date.
- **Floating Time**: Calendar exports use "Floating Time" to ensure deadlines stay at 11:59 PM regardless of your current timezone.
- **Manual MFA**: If a site requires login or MFA, you can interact with the cloud browser session via the "Live Viewer" link provided in the logs.
