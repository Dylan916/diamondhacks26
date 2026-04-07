# Course2Calendar 🎓

A power-user tool that automatically transforms messy course syllabus websites into a structured, synced calendar. Built with **Browser Use Cloud** and **Gemini 3.1 Flash**.

**No API tokens required. Works with any public course syllabus. Free with Gemini 3.1 Flash.**

## 🏆 DiamondHacks 2026
View our Devpost submission: [Course2Calendar on Devpost](https://devpost.com/software/course2calendar)

---

## ✨ Key Features

- **🚀 Parallel Multi-Sync**: Launch independent cloud browser sessions for all your courses at once.
- **🧠 AI Smart-Detection**: Gemini automatically extracts course names (e.g., "DSC 106") and codes directly from the raw syllabus text.
- **🕒 Floating Time Accuracy**: Deadlines are locked to 11:59 PM regardless of your timezone—no more 4:59 PM shifts!
- **🔄 Local SQLite Storage**: Assignments are persisted locally in a hidden `.data/` directory to avoid server reboot loops.
- **📅 Universal Export**: One-click download of a standard `.ics` file for Google Calendar, Apple Calendar, or Outlook.
- **🔏 Privacy First**: No course credentials or passwords are required or stored.

---

## 🛠️ Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Gemini API Key**: Get a free key at [aistudio.google.com](https://aistudio.google.com)
- **Browser Use API Key**: Get a cloud key at [cloud.browser-use.com](https://cloud.browser-use.com)

---

## 🚀 Quick Start

### 1. Configure Environment
```bash
cp .env.example .env
```
Fill in your `GEMINI_API_KEY` and `BROWSER_USE_API_KEY`.

### 2. Install Dependencies
```bash
# Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 3. Run the App
**Terminal 1 (Backend):**
```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```
**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```
Open [http://localhost:5173](http://localhost:5173).

---

## 📖 How to Use

1.  **Paste your URLs**: Enter your syllabus or course portals into the dashboard.
2.  **Start Sync**: Click "Start Sync" to launch the parallel cloud agents.
3.  **Watch Live**: Monitor the interleaved activity feed to see precisely what each agent is scanning.
4.  **Export**: Click "Export to Calendar" and drag the resulting `.ics` file into your favorite calendar app.

---

## 📄 License & Safety

Course2Calendar is designed for educational use. It scrapes only what you provide and stores everything locally on your machine.
