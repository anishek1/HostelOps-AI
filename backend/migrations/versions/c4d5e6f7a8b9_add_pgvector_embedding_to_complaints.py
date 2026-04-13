"""add pgvector embedding to complaints

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-04-03

Enables pgvector extension and adds embedding column (vector(384))
to the complaints table for semantic deduplication.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension (Supabase supports this natively)
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    op.add_column(
        'complaints',
        sa.Column('embedding', sa.Text(), nullable=True),
    )
    # Change the column type to vector(384) — must use raw SQL since
    # Alembic doesn't have native pgvector column type support
    op.execute(sa.text(
        "ALTER TABLE complaints ALTER COLUMN embedding TYPE vector(384) USING embedding::vector(384)"
    ))


def downgrade() -> None:
    op.drop_column('complaints', 'embedding')
