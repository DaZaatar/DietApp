# Architecture

## Style
Modular monolith with explicit module boundaries under `backend/app/modules`.

## Backend Layers
- API routers: module-scoped routers composed in `app/main.py`
- Services: business orchestration
- Repositories: deferred until needed
- Models: SQLAlchemy declarative models
- Schemas: Pydantic request/response contracts

## Cross-cutting
- `app/core/config.py`: env-driven settings
- `app/db/session.py`: engine/session factory
- `tracking/storage.py`: storage abstraction to allow local -> cloud migration

## Frontend Structure
Feature-first folders under `frontend/src/features` with shared app shell and api client.

## Data Ownership
- imports: parsing lifecycle and import logs
- tracking: meal completion + attachment metadata
- ai: model interaction and parsing retry/validation
- shopping: user-scoped checklist state and meal-plan-scoped aggregated ingredient view

## Shopping Data Model
- `meal_ingredients`: persisted ingredient rows per imported meal (`name`, `quantity`, `unit`, `category`)
- `shopping_checklist_entries`: per-user checked state for ingredient rows
- shopping API returns aggregated items grouped by `category + ingredient + unit`, with summed quantities
