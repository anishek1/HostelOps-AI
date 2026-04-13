"""add llm extraction fields to complaints

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-04-03

Adds urgency, affected_count, location, safety_flag, language_detected
to the complaints table. These replace the fake confidence_score routing.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('complaints', sa.Column('urgency', sa.Integer(), nullable=True))
    op.add_column('complaints', sa.Column('affected_count', sa.Integer(), nullable=True))
    op.add_column('complaints', sa.Column('location', sa.String(200), nullable=True))
    op.add_column('complaints', sa.Column('safety_flag', sa.Boolean(), nullable=True))
    op.add_column('complaints', sa.Column('language_detected', sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column('complaints', 'language_detected')
    op.drop_column('complaints', 'safety_flag')
    op.drop_column('complaints', 'location')
    op.drop_column('complaints', 'affected_count')
    op.drop_column('complaints', 'urgency')
