---
name: start-dev-servers
description: >-
  Starts the DietApp FastAPI backend (uvicorn) and Vite frontend dev servers.
  Use when the user asks to run, start, or launch the app locally, dev servers,
  backend, or frontend.
---

# Start dev servers

## Prerequisites

- Backend: Python venv in `backend/.venv` with `pip install -r requirements.txt`, and `backend/.env` with `DATABASE_URL` (see repo `README.md`).
- Frontend: `frontend/node_modules` from `npm install`.

## Ports

- Backend API: **8000** (default uvicorn).
- Frontend (Vite): **5173** (default).

Optional env: `VITE_API_BASE_URL` if you do not use the Vite dev proxy default (`/api/v1` → `http://127.0.0.1:8000`).

## Steps

Use **two terminals** from the repository root (`DietApp`).

### Terminal 1 — backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

If the venv is not at `.venv`, activate the project venv you use, then run the same `uvicorn` line.

### Terminal 2 — frontend

```powershell
cd frontend
npm run dev
```

## Verify

- Open `http://127.0.0.1:5173` for the UI.
- `GET http://127.0.0.1:8000/health` should return `{"status":"ok"}`.
