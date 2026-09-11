"""add document owner

Revision ID: 8ffaa0112c84
Revises: 4a060ec2b4a0
Create Date: 2026-09-09
"""

from alembic import op
import sqlalchemy as sa


revision = "8ffaa0112c84"
down_revision = "4a060ec2b4a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "owner_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_documents_owner_id"),
        "documents",
        ["owner_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_documents_owner_id_users",
        "documents",
        "users",
        ["owner_id"],
        ["id"],
    )

    # Assign any existing documents to the first admin user.
    op.execute(
        """
        UPDATE documents
        SET owner_id = (
            SELECT id
            FROM users
            WHERE role = 'admin'
            ORDER BY id
            LIMIT 1
        )
        WHERE owner_id IS NULL
        """
    )

    op.alter_column(
        "documents",
        "owner_id",
        existing_type=sa.Integer(),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_documents_owner_id_users",
        "documents",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_documents_owner_id"),
        table_name="documents",
    )

    op.drop_column(
        "documents",
        "owner_id",
    )
