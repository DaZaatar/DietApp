# DietApp

Adaptive Meal Management Platform built as a modular monolith.

## Stack
- Backend: FastAPI, PostgreSQL, SQLAlchemy, Alembic
- Frontend: React + TypeScript + Tailwind (shadcn/ui-ready structure)
- AI: OpenRouter via backend-only service clients

## Phase 1 Vertical Slices Included
- Import pipeline: upload PDF -> extract text -> AI parse -> JSON validation -> preview -> commit
- Tracking pipeline: update meal status (planned/eaten/skipped) + attach image to tracked meal
- Shopping checklist: per-user, per-meal-plan ingredient checklist with DB-persisted check state

## Start (Backend)
1. `cd backend`
2. `python -m venv .venv`
3. `.venv\\Scripts\\activate`
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill values
6. Provision local DBs: `powershell -ExecutionPolicy Bypass -File scripts/setup_dbs.ps1`
7. Seed sample tracking data: `python scripts/seed_tracking_data.py`
8. `uvicorn app.main:app --reload`

## Start (Frontend)
1. `cd frontend`
2. `npm install`
3. `npm run dev`

Set `VITE_API_BASE_URL` if backend is not on `http://localhost:8000/api/v1`.
Set `VITE_DEFAULT_USER_ID` to prefill API `X-User-Id` header in development.
