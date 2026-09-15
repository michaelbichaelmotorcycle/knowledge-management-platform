"""rename doc and chunk columns

Renames columns to match the field names assumed by the test suite
(Oli's contract): documents.id -> doc_id, documents.filename -> title,
document_chunks.id -> chunk_id, document_chunks.document_id -> doc_id.

Revision ID: a1b2c3d4e5f6
Revises: 8ffaa0112c84
Create Date: 2026-09-14 23:52:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "8ffaa0112c84"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- documents table: id -> doc_id, filename -> title ---
    op.drop_index(op.f("ix_documents_id"), table_name="documents")

    op.alter_column(
        "documents",
        "id",
        new_column_name="doc_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "documents",
        "filename",
        new_column_name="title",
        existing_type=sa.String(),
        nullable=False,
    )

    op.create_index(
        op.f("ix_documents_doc_id"),
        "documents",
        ["doc_id"],
        unique=False,
    )

    # --- document_chunks table: id -> chunk_id, document_id -> doc_id ---
    # The FK constraint on document_chunks.document_id references
    # documents.id, which no longer exists after the rename above, so we
    # must drop and recreate it pointing at documents.doc_id.
    op.drop_constraint(
        "document_chunks_document_id_fkey",
        "document_chunks",
        type_="foreignkey",
    )

    op.drop_index(op.f("ix_document_chunks_id"), table_name="document_chunks")

    op.alter_column(
        "document_chunks",
        "id",
        new_column_name="chunk_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "document_chunks",
        "document_id",
        new_column_name="doc_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.create_index(
        op.f("ix_document_chunks_chunk_id"),
        "document_chunks",
        ["chunk_id"],
        unique=False,
    )

    op.create_foreign_key(
        "document_chunks_doc_id_fkey",
        "document_chunks",
        "documents",
        ["doc_id"],
        ["doc_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "document_chunks_doc_id_fkey",
        "document_chunks",
        type_="foreignkey",
    )

    op.drop_index(op.f("ix_document_chunks_chunk_id"), table_name="document_chunks")

    op.alter_column(
        "document_chunks",
        "doc_id",
        new_column_name="document_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "document_chunks",
        "chunk_id",
        new_column_name="id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.create_index(
        op.f("ix_document_chunks_id"),
        "document_chunks",
        ["id"],
        unique=False,
    )

    op.create_foreign_key(
        "document_chunks_document_id_fkey",
        "document_chunks",
        "documents",
        ["document_id"],
        ["doc_id"],
    )

    op.drop_index(op.f("ix_documents_doc_id"), table_name="documents")

    op.alter_column(
        "documents",
        "title",
        new_column_name="filename",
        existing_type=sa.String(),
        nullable=False,
    )

    op.alter_column(
        "documents",
        "doc_id",
        new_column_name="id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.create_index(
        op.f("ix_documents_id"),
        "documents",
        ["id"],
        unique=False,
    )
