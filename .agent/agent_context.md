# Agent Context

## Product
Adaptive Meal Management Platform evolving from personal meal planning to multi-user.

## Current Phase
Phase 1 MVP foundations with vertical slices:
1. PDF upload/import parsing pipeline
2. Meal tracking status updates
3. Meal image attachment in tracking domain
4. Shopping checklist with DB-persisted check state

## Architectural Guardrails
- Modular monolith
- Backend: FastAPI + PostgreSQL + SQLAlchemy + Alembic
- Frontend: React + TypeScript + Tailwind + shadcn/ui-ready structure
- AI integrations only in backend via OpenRouter
- Imports module is PDF parsing only
- Tracking module owns meal status, notes, and image attachments
- Shopping module owns checklist read/write logic and user-scoped checked state

## Non-goals (for now)
- Multi-tenant RBAC implementation details
- AI analysis of meal images
- Complex pantry/nutrition logic
- Full ingredient normalization ontology
