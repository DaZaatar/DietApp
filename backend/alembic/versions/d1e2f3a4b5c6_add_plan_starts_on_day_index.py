"""add_plan_starts_on_and_day_index

Revision ID: d1e2f3a4b5c6
Revises: c4d8e9f0a1b2
Create Date: 2026-03-28 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "d1e2f3a4b5c6"
down_revision = "c4d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    mp_cols = {col["name"] for col in inspector.get_columns("meal_plans")}
    if "starts_on" not in mp_cols:
        op.add_column("meal_plans", sa.Column("starts_on", sa.Date(), nullable=True))

    day_cols = {col["name"] for col in inspector.get_columns("days")}
    if "day_index" not in day_cols:
        op.add_column("days", sa.Column("day_index", sa.Integer(), nullable=True))

    conn = bind
    plans = conn.execute(sa.text("SELECT id FROM meal_plans")).fetchall()
    for (plan_id,) in plans:
        rows = conn.execute(
            sa.text(
                """
                SELECT days.id FROM days
                JOIN weeks ON days.week_id = weeks.id
                WHERE weeks.meal_plan_id = :pid
                ORDER BY weeks.week_index ASC, days.id ASC
                """
            ),
            {"pid": plan_id},
        ).fetchall()
        for idx, (day_id,) in enumerate(rows):
            conn.execute(
                sa.text("UPDATE days SET day_index = :idx WHERE id = :did"),
                {"idx": idx, "did": day_id},
            )

    if bind.dialect.name == "postgresql":
        conn.execute(
            sa.text("UPDATE meal_plans SET starts_on = (created_at AT TIME ZONE 'UTC')::date WHERE starts_on IS NULL")
        )
    else:
        conn.execute(sa.text("UPDATE meal_plans SET starts_on = date(created_at) WHERE starts_on IS NULL"))


def downgrade() -> None:
    op.drop_column("days", "day_index")
    op.drop_column("meal_plans", "starts_on")
