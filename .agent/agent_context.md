# Agent Context

## Product
Adaptive Meal Management Platform evolving from personal meal planning to multi-user.

## Current Phase
Phase 1 MVP foundations with vertical slices:
1. PDF upload/import parsing pipeline (OpenRouter; requires `OPENROUTER_API_KEY` for real parsing)
2. Meal tracking status updates + ingredients in UI + image attachments
3. Shopping checklist with DB-persisted check state, multiple meal plans, category filters
4. Auth: register/login, HttpOnly cookie session, dev `X-User-Id` when enabled
5. Reporting: HTML tracking report for planned/eaten/skipped meals with date-range filters and daily/weekly/bi-weekly grouping (print/save as PDF)

## Architectural Guardrails
- Modular monolith
- Backend: FastAPI + PostgreSQL (production) / SQLite (local) + SQLAlchemy + Alembic
- Frontend: React + TypeScript + Tailwind + shadcn/ui-ready structure
- AI integrations only in backend via OpenRouter
- Imports module is PDF parsing only
- Tracking module owns meal status, notes, and image attachments
- Shopping module owns checklist read/write logic and user-scoped checked state
- Deployment: optional single-container Docker (API + static SPA same origin); Railway env vars for DB, JWT, CORS, cookie security

## Non-goals (for now)
- Multi-tenant RBAC implementation details
- AI analysis of meal images
- Complex pantry/nutrition logic
- Full ingredient normalization ontology
