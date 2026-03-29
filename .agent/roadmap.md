# Roadmap

## Phase 1 (in progress)
- [x] Repo scaffold and .agent docs
- [x] Backend app skeleton + DB foundation
- [x] Import vertical slice endpoints and services
- [x] Tracking status + image attachment backend endpoints
- [x] Frontend upload/preview + tracker scaffolding
- [x] Alembic first migration generation + apply
- [x] Shopping list backend + frontend view
- [x] Shopping list DB persistence (per-user checks) + meal-plan-scoped aggregated totals
- [x] Ingredient quantity/unit/category extraction contract in import parsing
- [x] End-to-end tests for import + tracking (+ shopping integration coverage)
- [x] Auth: register/login/logout/me, HttpOnly session cookie, JWT; login/register pages + redirect `next`
- [x] Ingredient category normalization + prompt tuning (canonical categories, Arabicizi note)
- [x] Shopping: multiple meal plans, delete meal plan, category filter chips
- [x] Tracker: ingredients + expandable card, sort eaten/skipped to bottom, status styling
- [x] Docker + Railway single-service deploy (static + API); Postgres URL handling; `PYTHONPATH` for Alembic

## Phase 2
- Ingredient normalization and merge logic
- Pantry exclusions in shopping list generation
- Tracking UX iteration and history improvements
- Persistent media storage (S3 or Railway volume) for production uploads

## Phase 3
- Auth/users/roles hardening (optional: refresh tokens, email verification)
- Pantry + nutrition logging
- AI chat + optional meal photo analysis
