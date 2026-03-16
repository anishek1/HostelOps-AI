"""sprint4_laundry_mess_models

Revision ID: c1cc0caedd71
Revises: a6d42d835175
Create Date: 2026-03-16 11:41:08.105586

Sprint 4 changes:
- laundry_slots: add slot_date, slot_time, booking_status, priority_score, booked_at, completed_at
- laundry_slots: make student_id, date, start_time, end_time nullable (Sprint 4 slots don't use them)
- laundry_slots: drop old non-nullable `status` column (replaced by `booking_status`)
- machines: add floor, status (MachineStatus enum), updated_at
- Create PostgreSQL enum types: laundryslostatus, machinestatus before adding columns
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c1cc0caedd71'
down_revision: Union[str, None] = 'a6d42d835175'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Create new PostgreSQL enum types BEFORE adding any columns that reference them
    op.execute("CREATE TYPE laundryslostatus AS ENUM ('available', 'booked', 'completed', 'cancelled')")
    op.execute("CREATE TYPE machinestatus AS ENUM ('operational', 'under_repair', 'out_of_service')")

    # Step 2: laundry_slots — add Sprint 4 columns
    op.add_column('laundry_slots', sa.Column('slot_date', sa.Date(), nullable=True))
    op.add_column('laundry_slots', sa.Column('slot_time', sa.String(length=20), nullable=True))
    # Add booking_status with a server default so existing rows are populated
    op.add_column('laundry_slots', sa.Column(
        'booking_status',
        sa.Enum('available', 'booked', 'completed', 'cancelled', name='laundryslostatus', create_type=False),
        nullable=False,
        server_default='available'
    ))
    op.add_column('laundry_slots', sa.Column('priority_score', sa.Float(), nullable=True))
    op.add_column('laundry_slots', sa.Column('booked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('laundry_slots', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))

    # Step 3: Make existing nullable-problem columns nullable
    op.alter_column('laundry_slots', 'student_id', existing_type=sa.UUID(), nullable=True)
    op.alter_column('laundry_slots', 'date', existing_type=sa.DATE(), nullable=True)
    op.alter_column('laundry_slots', 'start_time', existing_type=postgresql.TIME(), nullable=True)
    op.alter_column('laundry_slots', 'end_time', existing_type=postgresql.TIME(), nullable=True)

    # Step 4: Drop the old `status` column from laundry_slots (replaced by booking_status)
    op.drop_column('laundry_slots', 'status')

    # Step 5: machines — add Sprint 4 columns
    op.add_column('machines', sa.Column('floor', sa.Integer(), nullable=True))
    op.add_column('machines', sa.Column(
        'status',
        sa.Enum('operational', 'under_repair', 'out_of_service', name='machinestatus', create_type=False),
        nullable=False,
        server_default='operational'
    ))
    op.add_column('machines', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # machines
    op.drop_column('machines', 'updated_at')
    op.drop_column('machines', 'status')
    op.drop_column('machines', 'floor')

    # Restore old laundry_slots status column
    op.add_column('laundry_slots', sa.Column(
        'status',
        postgresql.ENUM('booked', 'cancelled', 'completed', 'no_show', name='slotstatus'),
        autoincrement=False,
        nullable=False,
        server_default='booked'
    ))

    # Restore not-null constraints
    op.alter_column('laundry_slots', 'end_time', existing_type=postgresql.TIME(), nullable=False)
    op.alter_column('laundry_slots', 'start_time', existing_type=postgresql.TIME(), nullable=False)
    op.alter_column('laundry_slots', 'date', existing_type=sa.DATE(), nullable=False)
    op.alter_column('laundry_slots', 'student_id', existing_type=sa.UUID(), nullable=False)

    # Drop Sprint 4 laundry columns
    op.drop_column('laundry_slots', 'completed_at')
    op.drop_column('laundry_slots', 'booked_at')
    op.drop_column('laundry_slots', 'priority_score')
    op.drop_column('laundry_slots', 'booking_status')
    op.drop_column('laundry_slots', 'slot_time')
    op.drop_column('laundry_slots', 'slot_date')

    # Drop the new enum types
    op.execute("DROP TYPE IF EXISTS laundryslostatus")
    op.execute("DROP TYPE IF EXISTS machinestatus")
