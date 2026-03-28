"""add_user_password_hash

Revision ID: c4d8e9f0a1b2
Revises: 8f3c2e1a4d7b
Create Date: 2026-03-28 23:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "c4d8e9f0a1b2"
down_revision = "8f3c2e1a4d7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "password_hash" not in columns:
        op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
