# ScheduleSystemAI

ScheduleSystemAI is an MVP for AI-assisted study planning. The first version does not require an LLM: it generates a daily study plan from `remaining_hours / remaining_days`, then recalculates the plan whenever the user records today's progress.

## Stack

- Frontend: Next.js App Router, TypeScript, Vercel-ready
- Backend: FastAPI, SQLAlchemy, Alembic, Railway-ready
- Database: PostgreSQL

## Repository Layout

```text
.
├── backend/   # FastAPI API, DB models, planner service
└── frontend/  # Next.js UI
```

## Quick Start

### 1. Start PostgreSQL

```bash
docker compose up -d db
```

### 2. Run the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`.

### 3. Run the frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

The app runs at `http://localhost:3000`.

## MVP Features

- Email/password signup and login
- Subject registration with deadline and required study hours
- Daily available study time setting
- Formula-based plan generation
- Today's check-in with actual study hours
- Automatic plan recalculation after every check-in
- Capacity warning when today's planned hours exceed available hours

## Planning Formula

For each active subject:

```text
remaining_hours = required_hours - completed_hours
remaining_days = deadline_date - today + 1
planned_hours_per_day = remaining_hours / remaining_days
```

Gemini Flash can be added later by replacing the planner implementation behind the same API surface.

## Deployment Notes

### Vercel Frontend

- Project root: `frontend`
- Build command: `npm run build`
- Output: Next.js default
- Environment variables:
  - `NEXT_PUBLIC_API_BASE_URL=https://your-railway-api.example.com`

### Railway Backend

- Project root: `backend`
- Database: Railway PostgreSQL
- Environment variables:
  - `DATABASE_URL` from Railway PostgreSQL
  - `SECRET_KEY` with a long random value
  - `BACKEND_CORS_ORIGINS=https://your-vercel-app.vercel.app`
  - `CREATE_TABLES_ON_STARTUP=true` for MVP
- Start command if not using Docker: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

For production hardening, switch `CREATE_TABLES_ON_STARTUP=false` and run Alembic migrations during deploy.

### Vercel Backend Alternative

If Railway is unavailable, the FastAPI backend can also run on Vercel.

- Create a second Vercel project from the same repository.
- Set Root Directory to `backend`.
- Set Framework Preset to `Other`.
- Keep Build Command empty unless Vercel asks for one.
- Add environment variables:
  - `DATABASE_URL` from Neon or another hosted PostgreSQL provider
  - `SECRET_KEY` with a long random value
  - `BACKEND_CORS_ORIGINS=https://your-frontend.vercel.app`
  - `CREATE_TABLES_ON_STARTUP=true`

The backend root URL should return a JSON status response. `/health` should return `{"status":"ok"}`.

Do not deploy the repository root as a single Vercel project for this MVP. Use two Vercel projects:

1. `frontend` as the Next.js app
2. `backend` as the FastAPI API

If Vercel shows "No FastAPI entrypoint found" while listing `backend/app/main.py` or `backend/index.py`, the project is probably using the repository root. Either set Root Directory to `backend`, or keep the repository root and let `pyproject.toml` point Vercel to `backend.index:app`.

If Vercel shows `500: FUNCTION_INVOCATION_FAILED`, open the backend deployment logs first. The most common cause is a missing or invalid `DATABASE_URL`. `/health` returns database status when the app boots far enough to respond.
