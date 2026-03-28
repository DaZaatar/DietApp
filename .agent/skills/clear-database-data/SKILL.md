---
name: clear-database-data
description: >-
  Removes all application rows from the DietApp database while keeping tables
  and Alembic migration history. Use when the user asks to wipe, reset, truncate,
  or clear DB data (not schema), empty the database, or delete all records.
---

# Clear database data (keep tables)

## What it does

- Deletes rows from all application tables in **foreign-key-safe order**.
- Does **not** drop tables or remove `alembic_version` (migration state stays).
- Does **not** delete files under `backend/uploads` (or other local media paths); only DB rows for attachments are removed. Optionally delete orphaned files manually if needed.

## How to run

From the repository root, with the same `DATABASE_URL` as the running app (typically via `backend/.env`):

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts/clear_db_data.py
```

`DATABASE_URL` must match the app: usually `backend/.env` (pydantic-settings loads `.env` from the **current working directory**, so run the command from `backend` like uvicorn).

## When the backend is running

Stop the backend first, or run this in a separate shell. Avoid concurrent writes during the delete.

## Script location

Implementation: `backend/scripts/clear_db_data.py` (single source of truth for table delete order).
