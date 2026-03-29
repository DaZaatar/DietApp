# Architecture

## Style
Modular monolith with explicit module boundaries under `backend/app/modules`.

## Backend Layers
- API routers: module-scoped routers composed in `app/api/router.py`; optional SPA static mount in `app/main.py` when `STATIC_ROOT` is set (Docker/Railway).
- Services: business orchestration
- Repositories: deferred until needed
- Models: SQLAlchemy declarative models
- Schemas: Pydantic request/response contracts

## Cross-cutting
- `app/core/config.py`: env-driven settings (Postgres URL normalization for Railway, optional `static_root`, `cookie_secure`, ingredient category normalization via `imports/ingredient_categories.py`)
- `app/db/session.py`: engine/session factory
- `app/api/deps.py`: `get_current_user_id` (Bearer JWT, HttpOnly `access_token` cookie, then dev `X-User-Id` / default); `get_session_user_id_strict` for `/auth/me`
- `tracking/storage.py`: local file storage for meal images; delete files when meal plans are removed

## Auth
- `auth`: register/login (sets HttpOnly cookie), logout, `/auth/me`; passwords hashed with pbkdf2_sha256; JWT for cookie value
- Production: disable dev header defaults via env (`ALLOW_DEV_USER_HEADER`, `ALLOW_DEFAULT_USER`)

## Frontend Structure
Feature-first folders under `frontend/src/features` with shared app shell, `pages/` for Import, Tracking, Shopping, Login, Register. API client uses `credentials: "include"`; default `VITE_API_BASE_URL` is `/api/v1` (Vite proxy in dev, same origin in production Docker).

## Data Ownership
- imports: parsing lifecycle and import logs
- tracking: meal completion + attachment metadata
- ai: OpenRouter integration only
- meal_plans: list + delete meal plans (cascades shopping/tracking data; attachment files deleted from disk)
- shopping: user-scoped checklist state and meal-plan-scoped aggregated ingredient view

## Shopping Data Model
- `meal_ingredients`: persisted ingredient rows per imported meal (`name`, `quantity`, `unit`, `category`)
- `shopping_checklist_entries`: per-user checked state for ingredient rows
- shopping API returns aggregated items grouped by `category + ingredient + unit`, with summed quantities

## Deployment
- Root `Dockerfile`: build Vite `dist`, copy to `/app/static`, `PYTHONPATH=/app`, `entrypoint.sh` runs `alembic upgrade head` then uvicorn on `PORT`
- Railway: Postgres `DATABASE_URL` referenced into the service; env vars documented in README
