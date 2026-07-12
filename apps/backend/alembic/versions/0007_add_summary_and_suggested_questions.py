"""add summary and suggested_questions to documents

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-12

"""
import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("suggested_questions", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "suggested_questions")
    op.drop_column("documents", "summary")
