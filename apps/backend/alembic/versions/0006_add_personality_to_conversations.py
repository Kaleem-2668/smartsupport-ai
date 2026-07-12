"""add personality column to conversations

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-12

"""
import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column(
            "personality",
            sa.String(length=20),
            nullable=False,
            server_default="professional",
        ),
    )


def downgrade() -> None:
    op.drop_column("conversations", "personality")
