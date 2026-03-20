"""add_no_show_to_laundryslostatus_enum

Revision ID: 8d59bc56aa84
Revises: 80db1c48cf9d
Create Date: 2026-03-17 13:54:17.910732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d59bc56aa84'
down_revision: Union[str, None] = '80db1c48cf9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE laundryslostatus ADD VALUE IF NOT EXISTS 'no_show'")

def downgrade() -> None:
    pass
