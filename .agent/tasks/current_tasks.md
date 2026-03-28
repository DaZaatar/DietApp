# Current Tasks

## Recently Completed
- Added ingredient-level import contract (`name`, `quantity`, `unit`, `category`) in OpenRouter parsing schema.
- Persisted `meal_ingredients` and `shopping_checklist_entries` in DB with Alembic migrations.
- Implemented user-scoped shopping checklist persistence endpoint (`PATCH /shopping/items/{item_key}`).
- Switched shopping list API to meal-plan-scoped aggregated totals by ingredient+unit, ordered by category.
- Updated shopping UI to expandable animated card with checklist rows grouped by category.
- Added and maintained integration coverage for import/tracking/shopping behaviors.

## Remaining TODOs
- Re-import real meal plan PDFs to populate category-quality data from parser output.
- Add stricter validation/normalization for ingredient category values before persistence.
- Add shopping API tests for category ordering edge cases and invalid category payload recovery.
- Replace auth stub with real current-user context (remove header-only reliance in production).

## Follow-up Steps
1. Validate parser output quality on 2-3 real PDFs and tune prompt examples for category accuracy.
2. Add optional category filters in shopping UI (for faster in-store checklist workflows).
3. Introduce canonical ingredient normalization mapping in Phase 2.
