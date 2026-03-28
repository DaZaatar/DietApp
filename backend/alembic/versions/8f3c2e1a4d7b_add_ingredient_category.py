"""add_ingredient_category

Revision ID: 8f3c2e1a4d7b
Revises: 5a6b1d9f0b2c
Create Date: 2026-03-28 22:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8f3c2e1a4d7b"
down_revision = "5a6b1d9f0b2c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("meal_ingredients")}
    if "category" not in columns:
        op.add_column(
            "meal_ingredients",
            sa.Column("category", sa.String(length=50), nullable=False, server_default="other"),
        )


def downgrade() -> None:
    op.drop_column("meal_ingredients", "category")
