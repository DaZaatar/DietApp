"""add_original_meal_fields

Revision ID: e7f9a1b2c3d4
Revises: d1e2f3a4b5c6
Create Date: 2026-03-30 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "e7f9a1b2c3d4"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("meals")}

    if "original_meal_type" not in columns:
        op.add_column("meals", sa.Column("original_meal_type", sa.String(length=30), nullable=True))
    if "original_title" not in columns:
        op.add_column("meals", sa.Column("original_title", sa.String(length=255), nullable=True))

    bind.execute(
        sa.text(
            """
            UPDATE meals
            SET original_meal_type = meal_type
            WHERE original_meal_type IS NULL
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE meals
            SET original_title = title
            WHERE original_title IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_column("meals", "original_title")
    op.drop_column("meals", "original_meal_type")
