# ⚡ ThePromptTool

**ThePromptTool** is a modern, full-stack application designed to orchestrate and deliver a "Daily Prompt" experience. It captures high-quality AI prompts from Anthropic's official library and serves them to users with a gauranteed unique, one-time-reveal mechanism.

---

## 🌟 Key Features

- **Automated Ingestion**: High-fidelity scraper using Playwright to extract system and user prompts directly from Anthropic's technical documentation.
- **Atomic Selection**: Proprietary selection logic using PostgreSQL `SKIP LOCKED` to ensure prompts are served exactly once across all sessions.
- **Neon Codex UI**: A premium, "cyber-grimoire" inspired interface with typewriter reveals, theme toggling, and rich micro-animations.
- **Prompt Coach Mode**: Enhanced "Try on Claude" integration that prepends a professional prompt engineering pedagogy to help users learn the anatomy of elite prompts.
- **One-Click Execution**: Integrated functionality that pre-fills specialized prompts into the Claude.ai chat interface.
- **Flexible Reliability**: Built-in support for both PostgreSQL (Production/High Concurrency) and SQLite (Local Development/Lite Deployment).

---

## 🏗️ Technical Architecture

### Tech Stack
- **Frontend**: React 18, Vite, Vanilla CSS (Design Tokens, HSL tailors).
- **Backend**: Python 3.11, Flask, SQLAlchemy.
- **Scraper**: Playwright (Chromium), Regex-based API pattern extraction.
- **Database**: PostgreSQL (Default) / SQLite (Fallback).
- **DevOps**: GitHub Actions (CI), Railway (API/DB), Vercel (Frontend).

### Project Structure
```text
ThePromptTool/
├── backend/
│   ├── scripts/          # Scrapers and DB utilities
│   ├── services/         # Core business logic (Atomic Serving)
│   ├── models.py         # SQLAlchemy schemas
│   └── app.py            # Flask Entry point
├── frontend/
│   ├── src/
│   │   ├── components/   # Modular UI elements
│   │   ├── hooks/        # Custom state management
│   │   └── App.jsx       # Main Orchestrator
│   └── index.css         # Design System (Neon Codex)
└── docs/                 # Documentation and Deep Dives
```

---

## 🚀 Getting Started

### Easy Start (Unified Commands)

If you have Node.js and Python installed, you can manage the project from the root directory:

```bash
# Initial Setup
npm run setup

# Run Frontend
npm run dev

# Run Backend (separate terminal)
npm run dev:backend
```

---

### Manual Setup (Subdirectories)

#### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Optional: Seed the database
playwright install chromium
python scripts/scrape_prompts.py
python app.py
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🔧 Database Configuration

By default, the application uses **SQLite** for local development. To use **PostgreSQL**, simply update the `DATABASE_URL` in your `.env` file. The application automatically detects the driver and switches between atomic selection strategies (`FOR UPDATE SKIP LOCKED` for Postgres vs manual transactions for SQLite).

---

## 📜 License
MIT © 2026
