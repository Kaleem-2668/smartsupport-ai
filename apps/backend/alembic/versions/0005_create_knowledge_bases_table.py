"""create knowledge bases table and add foreign key to documents

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-04

"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_bases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_knowledge_bases_user_id", "knowledge_bases", ["user_id"])

    # Add knowledge_base_id to documents table (nullable for backward compatibility)
    op.add_column(
        "documents",
        sa.Column(
            "knowledge_base_id",
            sa.Uuid(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_documents_knowledge_base_id",
        "documents",
        "knowledge_bases",
        ["knowledge_base_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_documents_knowledge_base_id", "documents", ["knowledge_base_id"])


def downgrade() -> None:
    op.drop_index("ix_documents_knowledge_base_id", table_name="documents")
    op.drop_constraint("fk_documents_knowledge_base_id", "documents", type_="foreignkey")
    op.drop_column("documents", "knowledge_base_id")
    op.drop_index("ix_knowledge_bases_user_id", table_name="knowledge_bases")
    op.drop_table("knowledge_bases")
