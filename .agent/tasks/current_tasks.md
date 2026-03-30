# Current Tasks

## Recently Completed
- OpenRouter prompt categories (meats, dairy, bread, grains, etc.) + Arabicizi guidance; import persistence + category normalization module.
- JWT + HttpOnly cookie auth, `/auth/me`, login/register pages, `next` redirect, remember-me via cookie max-age; Vite proxy + `/api/v1` default.
- Shopping: list all meal plans, per-plan expandable cards, delete meal plan (DB + attachment files on disk).
- Tracker: ingredients per meal, expandable UI, eaten/skipped ordering and styling.
- Reports: tracking HTML report endpoint (`/tracking/reports/html`) with date range + daily/weekly/bi-weekly grouping; new frontend Reports page with printable/PDF-friendly flow.
- Docker/Railway: root Dockerfile, `entrypoint.sh`, `PYTHONPATH`, `Settings` for `DATABASE_URL` + Railway errors, Postgres URL normalization.
- Integration tests expanded (auth cookie, shopping order, meal plan delete, attachment file cleanup).
- `.agent/skills` for start/stop dev servers and clear DB data.

## Remaining TODOs
- Re-import real meal plan PDFs to validate parser categories and transliterations.
- Stricter validation/normalization for ingredient `category` edge cases (optional extra tests).
- Optional: dedicated binary PDF export endpoint (server-side rendering), currently browser print-to-PDF from HTML report.
- Production: Railway volume or object storage for `uploads/` (ephemeral disk on Railway).
- Optional: refresh tokens, stricter rate limits on auth endpoints.

## Follow-up Steps
1. Validate parser on 2–3 real PDFs; tune prompts if categories drift.
2. Phase 2: canonical ingredient merge + pantry exclusions in shopping.
3. Clear production DB: use `railway run` + `scripts/clear_db_data.py` or SQL (see agent skill / README).
