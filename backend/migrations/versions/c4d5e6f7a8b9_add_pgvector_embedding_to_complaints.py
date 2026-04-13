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
from sqlalchemy.exc import ProgrammingError

revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension.
    # On Supabase (the primary target) this works without superuser.
    # On other managed Postgres (RDS, Azure, etc.) this requires superuser
    # or the extension must be pre-installed. If this step fails, run:
    #   CREATE EXTENSION IF NOT EXISTS vector;
    # as a superuser and then re-run `alembic upgrade head`.
    try:
        op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    except ProgrammingError as e:
        raise SystemExit(
            "\n\n[MIGRATION ERROR] Cannot create pgvector extension.\n"
            "This step requires superuser privileges on PostgreSQL.\n"
            "\nFix options:\n"
            "  1. Supabase: enable pgvector in the dashboard under Database → Extensions.\n"
            "  2. Other managed Postgres: connect as superuser and run:\n"
            "       CREATE EXTENSION IF NOT EXISTS vector;\n"
            "     then re-run: alembic upgrade head\n"
            f"\nOriginal error: {e}\n"
        ) from e
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
