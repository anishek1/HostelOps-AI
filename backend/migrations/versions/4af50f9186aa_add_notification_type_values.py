"""add_notification_type_values

Revision ID: 4af50f9186aa
Revises: 7f928dfccad1
Create Date: 2026-03-19 01:10:45.403399

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4af50f9186aa'
down_revision: Union[str, None] = '7f928dfccad1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'registration_approved'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'registration_rejected'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'password_reset'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'account_deactivated'")


def downgrade() -> None:
    pass
