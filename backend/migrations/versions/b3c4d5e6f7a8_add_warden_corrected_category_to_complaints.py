"""add warden_corrected_category to complaints

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-04-03

Adds warden_corrected_category column to complaints table.
Used for AI accuracy analytics — tracks when wardens correct AI classifications.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'complaints',
        sa.Column(
            'warden_corrected_category',
            sa.Enum(
                'mess', 'laundry', 'maintenance', 'interpersonal', 'critical', 'uncategorised',
                name='complaintcategory',
                create_type=False,  # enum already exists
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column('complaints', 'warden_corrected_category')
