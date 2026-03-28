"""Delete all application data rows; keeps schema and alembic_version intact."""

import sys
from pathlib import Path

# Allow `python scripts/clear_db_data.py` from `backend` without PYTHONPATH.
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine

# Child tables first (FK order).
_TABLES = (
    "shopping_checklist_entries",
    "meal_attachments",
    "meal_tracking_entries",
    "meal_ingredients",
    "meals",
    "days",
    "weeks",
    "meal_plans",
    "users",
)


def main() -> None:
    with engine.begin() as conn:
        for table in _TABLES:
            conn.execute(text(f"DELETE FROM {table}"))
    print(f"Cleared data from {len(_TABLES)} tables (DATABASE_URL={settings.database_url!r}).")


if __name__ == "__main__":
    main()
