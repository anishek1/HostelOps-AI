"""add_warden_override_to_classifiedby_enum

Revision ID: a6d42d835175
Revises: 2d36eb8e82cf
Create Date: 2026-03-13 01:13:16.225646

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6d42d835175'
down_revision: Union[str, None] = '2d36eb8e82cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE classifiedby ADD VALUE IF NOT EXISTS 'warden_override'")

def downgrade() -> None:
    pass  # Postgres doesn't support removing enum values
