"""add_meal_ingredients_and_shopping_checklist

Revision ID: 5a6b1d9f0b2c
Revises: 38003a9a440b
Create Date: 2026-03-28 22:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5a6b1d9f0b2c"
down_revision = "38003a9a440b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meal_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meal_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.String(length=50), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["meal_id"], ["meals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "shopping_checklist_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("meal_ingredient_id", sa.Integer(), nullable=False),
        sa.Column("checked", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["meal_ingredient_id"], ["meal_ingredients.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "meal_ingredient_id", name="uq_user_meal_ingredient_check"),
    )


def downgrade() -> None:
    op.drop_table("shopping_checklist_entries")
    op.drop_table("meal_ingredients")
