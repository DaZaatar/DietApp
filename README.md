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

Default API base is `/api/v1` (Vite dev proxy and production Docker). Override with `VITE_API_BASE_URL` only if the API is on another origin.

Set `VITE_DEFAULT_USER_ID` to prefill API `X-User-Id` header in development.

## Deploy on Railway (single service)

The repo includes a root **`Dockerfile`**: it builds the Vite app, copies `dist` into the image, runs **`alembic upgrade head`**, then **uvicorn**. The API and SPA share one origin so session cookies work.

1. **New project** → **Deploy from GitHub** → select this repo.
2. Add **PostgreSQL** (Variables → `DATABASE_URL` is injected when you connect the plugin).
3. Set variables (example):
   - **`JWT_SECRET`**: long random string.
   - **`OPENROUTER_API_KEY`**: your key (if using imports).
   - **`CORS_ORIGINS`**: your public app URL, e.g. `https://YOUR_SERVICE.up.railway.app` (comma-separated if several).
   - **`COOKIE_SECURE`**: `true` (HTTPS on Railway).
   - **`ALLOW_DEV_USER_HEADER`**: `false`
   - **`ALLOW_DEFAULT_USER`**: `false` (forces real login in production).
4. **Generate domain** (Settings → Networking) and open the URL. `/health` should return `{"status":"ok"}`.

**Uploads:** meal images are stored under `MEDIA_LOCAL_ROOT` (default `uploads`) on disk. On Railway the filesystem is ephemeral unless you attach a **volume** and set `MEDIA_LOCAL_ROOT` to a path on that volume.
