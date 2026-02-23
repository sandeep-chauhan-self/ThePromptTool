# 🚀 ThePromptTool — Complete Railway & Vercel Deployment Guide

This guide provides step-by-step instructions for deploying the **ThePromptTool** application. 
The architecture consists of a React (Vite) frontend deployed on **Vercel**, and a Python (Flask) backend with a PostgreSQL database deployed on **Railway**.

---

## 1. Environment Files

You must configure environment variables on both platforms. Below are the required variables for each.

### 1a. Backend Environment (`backend/.env`)
These variables must be added to your **Railway** backend service.

```env
# ─── Flask Core ───────────────────────────────────────────────
FLASK_APP=app.py
FLASK_ENV=production          # Set to production for live deployment
SECRET_KEY=your-secret-key-here   # Generate a unique key using: python -c "import secrets; print(secrets.token_hex(32))"

# ─── Database ─────────────────────────────────────────────────
# Railway auto-injects this when you add a Postgres service.
DATABASE_URL=postgresql://user:password@host:port/dbname

# ─── CORS ─────────────────────────────────────────────────────
# Replace this with your actual Vercel frontend URL once deployed
FRONTEND_URL=https://your-app.vercel.app
```

### 1b. Frontend Environment (`frontend/.env`)
These variables must be added to your **Vercel** frontend project.

```env
# ─── API Base URL ─────────────────────────────────────────────
# Replace this with your actual Railway backend URL once deployed
VITE_API_URL=https://your-backend.up.railway.app
```

⚠️ **Gotcha:** Never commit your real `.env` files to GitHub. Ensure `backend/.env` and `frontend/.env` are in your `.gitignore` file.

---

## 2. Pre-Deployment Checklist (Local)

Before deploying to the cloud, ensure the application runs perfectly on your local machine using the unified root commands.

```bash
# 1. Install all dependencies from the project root
npm run setup

# 2. Start the Backend (in Terminal 1)
npm run dev:backend

# 3. Start the Frontend (in Terminal 2)
npm run dev:frontend
```
Open `http://localhost:5174` (or 5173 depending on Vite) and verify the UI loads and successfully fetches a prompt from the local SQLite database.

---

## 3. Railway Setup — PostgreSQL Database Service

We will set up the database first so we can inject its URL into the backend.

**Step 1.** Go to [railway.app](https://railway.app) and log in. Click **New Project**.

**Step 2.** Click **Add a Service** → **Database** → **PostgreSQL**.
Railway will immediately provision a Postgres instance and generate credentials.

**Step 3.** Click your new PostgreSQL service → go to the **Variables** tab.
You will see a variable named `DATABASE_URL`. Railway will use this to connect your backend natively.

⚠️ **Gotcha:** Railway's `DATABASE_URL` uses the `postgresql://` scheme. If older SQLAlchemy versions complain, the backend `config.py` already includes a compatibility fix to handle `postgres://` vs `postgresql://`.

---

## 4. Railway Setup — Flask Backend Service

**Step 1.** In the same Railway project, click **New** (or **Add a Service**) → **GitHub Repo**.
Select the `sandeep-chauhan-self/ThePromptTool` repository.

**Step 2.** Configure the Service:
- Click the newly added GitHub service.
- Go to the **Settings** tab.
- Scroll down to **Root Directory** and type `/backend`. Hit Enter.
- Ensure the **Build Command** is empty (Railway auto-detects `requirements.txt`).
- Ensure the **Start Command** is empty (Railway auto-detects `Procfile` or `app.py`).

**Step 3.** Link the Database:
- Go to the **Variables** tab of your Backend service.
- Click **Add Reference Variable**.
- Select your PostgreSQL service and choose `DATABASE_URL`. This securely links the database.

**Step 4.** Add Remaining Environment Variables:
Click **Add Variable** for each of the following:

| Variable | Value |
|---|---|
| `FLASK_APP` | `app.py` |
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | *(Generate a random 64-char hex string)* |
| `FRONTEND_URL` | *(Leave blank for now; we will update this after Step 5)* |
| `PORT` | `5000` |

**Step 5.** Trigger a Deploy.
Go to the **Deployments** tab. Railway will build the Python environment.
Once complete, go to **Settings** → **Networking** → **Generate Domain**.
Copy this URL (e.g., `https://theprompttool-backend.up.railway.app`).

---

## 5. Vercel Setup — React Frontend

Now we deploy the frontend and point it to the Railway backend.

**Step 1.** Go to [vercel.com](https://vercel.com) → **Add New Project** → Import the `sandeep-chauhan-self/ThePromptTool` repository.

**Step 2.** Configure the Project:
- Open the **Root Directory** settings and click **Edit**. Select `/frontend`.
- Vercel will auto-detect **Vite**. Leave Build Command as `npm run build` and Output Directory as `dist`.

**Step 3.** Add Environment Variables:
Expand the **Environment Variables** section and add:

| Variable | Value |
|---|---|
| `VITE_API_URL` | *(Paste your Railway Backend URL from Step 4, e.g., `https://theprompttool-backend.up.railway.app`)* |

**Step 4.** Click **Deploy**. Vercel will build the React app.
Once finished, Vercel will provide a live URL (e.g., `https://theprompttool.vercel.app`). Copy this URL.

---

## 6. Finalizing CORS Configuration

The backend needs to know it is allowed to accept requests from your new Vercel domain.

**Step 1.** Go back to [Railway](https://railway.app).
**Step 2.** Click your Backend service → **Variables** tab.
**Step 3.** Add or update the `FRONTEND_URL` variable:
- Set it to your exact Vercel URL (e.g., `https://theprompttool.vercel.app`). **Do not include a trailing slash.**
**Step 4.** Railway will automatically redeploy the backend with the new CORS configuration.

---

## 7. Database Initialization on Railway

Because the Railway Postgres database is completely empty, you must create the tables before the app can serve prompts.

**Option A — Railway Dashboard (Easiest)**
1. In Railway, click your Backend service.
2. Go to the **Deployments** tab, find the latest successful deploy, and click **View Logs**.
3. At the top of the logs window, there is a **Command** box to run one-off tasks.
4. Run: `python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"`

**Option B — Local Scraper Execution**
You can run the scraper locally, but point it at the live database to securely upload the prompts.
1. Open your local terminal.
2. Activate the backend virtual environment.
3. Run the following command (replace with your actual Railway `DATABASE_URL`):
```bash
# Windows PowerShell
$env:DATABASE_URL="postgresql://postgres:password_from_railway@roundhouse.proxy.rlwy.net:12345/railway"
python scripts/scrape_prompts.py
```

---

## 8. Final Health Check

Run through this checklist to verify your production application is fully functional.

✅ **Backend Root Check**
```bash
curl https://[your-railway-url].up.railway.app/health
# Expected: {"status": "ok"}
```

✅ **Frontend Load Check**
Open `https://[your-vercel-url].vercel.app` in your browser. The Neon Codex UI should render instantly.

✅ **API CORS Check**
Right-click on the browser page, select **Inspect**, and go to the **Network** tab. 
Wait for the initial `/api/prompt/daily` call. It should return a `200 OK` status and not a CORS error.
If you see a `503 Service Unavailable`, ensure you ran the Database Initialization (Step 7) to create the `prompts` table.
