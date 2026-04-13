"""drop push_subscriptions table

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-04-14

Push notifications were removed in Sprint F. The push_subscriptions table
was created by migration 80db1c48cf9d but has no corresponding ORM model,
service, or route in the current codebase. This migration removes it cleanly.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the orphaned push_subscriptions table left over from Sprint 5.
    # Uses IF EXISTS so this is safe on databases that somehow never received
    # the original push_subscriptions creation (out-of-order migration runs).
    op.execute(sa.text("DROP TABLE IF EXISTS push_subscriptions"))


def downgrade() -> None:
    # Recreate the table so downgrade to c4d5e6f7a8b9 works correctly.
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('endpoint', sa.String(length=2000), nullable=False),
        sa.Column('p256dh', sa.String(length=200), nullable=False),
        sa.Column('auth', sa.String(length=100), nullable=False),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('endpoint'),
    )
