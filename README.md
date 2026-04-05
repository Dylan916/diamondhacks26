# Student Life Autopilot 🎓

A tool that logs into Canvas with your credentials, scrapes all your assignments and deadlines using a Browser Use AI agent, and pushes everything into a Notion database you can view as a calendar.

**No Canvas API token required. Works at any school. Free with Gemini Flash.**

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- A free Gemini API key from [aistudio.google.com](https://aistudio.google.com)
- A Notion account with an integration token

---

## 1 — Set up the Notion Database

1. Go to [notion.so](https://notion.so) and create a new **full-page database** (Table view).
2. Name it anything (e.g. "Canvas Assignments").
3. Add these properties **exactly** (names and types must match):

| Property name | Type   | Options (for Select fields)                                    |
|---------------|--------|----------------------------------------------------------------|
| Name          | Title  | (default, already exists)                                      |
| Course        | Text   |                                                                |
| Due Date      | Date   |                                                                |
| Type          | Select | Assignment, Exam, Midterm, Final, Project, Reading, Other      |
| Source        | Select | Assignments, Syllabus, Announcement, External Site             |
| Needs Review  | Checkbox |                                                              |

4. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations), create a new integration, copy the **Internal Integration Token**.
5. Open your database page in Notion, click **···** (top right) → **Connect to** → select your integration.
6. Copy the **Database ID** from the URL:
   `https://notion.so/YourWorkspace/<DATABASE_ID>?v=...`

---

## 2 — Configure Environment

```bash
cp .env.example .env
```

Fill in `.env`:
```
GEMINI_API_KEY=your_key_from_aistudio
NOTION_TOKEN=secret_your_integration_token
NOTION_DATABASE_ID=your_32char_database_id
```

---

## 3 — Install Backend Dependencies

```bash
cd /path/to/student-life-autopilot

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt

# Install Playwright browser (must be done separately)
playwright install chromium
```

---

## 4 — Install Frontend Dependencies

```bash
cd frontend
npm install
```

---

## 5 — Run the App

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

## 6 — Using the App

1. Enter your Canvas URL (e.g. `https://sdsu.instructure.com`)
2. Enter your Canvas username and password
3. Click **Sync Canvas**
4. A browser window will open — complete any MFA/Duo prompt manually
5. Watch the live activity log as the agent scrapes your assignments
6. When sync completes, your assignments appear as cards and in Notion

**To view as a calendar in Notion:**
Open your Notion database → click the layout selector → choose **Calendar** → select **Due Date** as the date field.

---

## Notes

- Canvas credentials are **never stored**. They are used only for the duration of the sync and discarded.
- Duplicate assignments are skipped automatically (matched by title + course + due date).
- The browser window is intentionally **not headless** so you can complete Duo/MFA if your school requires it.
