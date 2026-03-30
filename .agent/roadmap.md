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
- [x] Tracking reports: date-range HTML report with daily/weekly/bi-weekly grouping and print-to-PDF flow
- [x] Tracking reports v2: swap-aware imported-vs-current columns, inline attachment images, and 2-week plan cross-check mode
- [x] Tracker media UX: per-meal image viewer button, expandable full-size preview
- [x] Tracker day-level status: computed `active/completed/ended` + non-active days moved toward end

## Phase 2
- Ingredient normalization and merge logic
- Pantry exclusions in shopping list generation
- Tracking UX iteration and history improvements
- Persistent media storage (S3 or Railway volume) for production uploads

## Phase 3
- Auth/users/roles hardening (optional: refresh tokens, email verification)
- Pantry + nutrition logging
- AI chat + optional meal photo analysis
