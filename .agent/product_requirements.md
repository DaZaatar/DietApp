# Product Requirements

## MVP Scope
- Upload bi-weekly meal plan PDF
- Extract text and parse into structured JSON meals
- Split into weeks
- Preview/edit-ready payload endpoint
- Generate shopping list from imported meals (initial placeholder)
- Track planned/eaten/skipped meal state
- Attach meal images to tracking entries
- Generate tracking status reports (HTML/print-to-PDF) over selectable date ranges and groupings

## Separation of Concerns
- Imports module handles PDF parsing orchestration only
- Tracking module handles notes/status/eaten timestamp/image attachment

## Responsive UX Requirements
- Mobile-first and touch-friendly
- No hover-only key interactions
- No horizontal overflow on phone widths
- Quick upload/import flow and fast checklist actions