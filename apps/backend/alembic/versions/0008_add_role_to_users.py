"""add role column to users

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-13

"""
import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
