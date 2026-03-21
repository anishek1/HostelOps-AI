"""sprint7_multi_tenant

Revision ID: a1b2c3d4e5f6
Revises: 4af50f9186aa
Create Date: 2026-03-21 00:00:00.000000

Sprint 7: Multi-tenant architecture.
- Creates hostels table
- Adds nullable hostel_id FK to: users, complaints, machines, laundry_slots,
  mess_feedback, mess_alerts, hostel_config
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '4af50f9186aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure hostelmode enum exists — safe to run even if it already exists
    op.execute(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'hostelmode') THEN "
        "CREATE TYPE hostelmode AS ENUM ('college', 'autonomous'); "
        "END IF; "
        "END $$;"
    )

    # 1. Create hostels table — references existing hostelmode enum (create_type=False)
    op.create_table(
        'hostels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column(
            'mode',
            postgresql.ENUM('college', 'autonomous', name='hostelmode', create_type=False),
            nullable=False,
        ),
        sa.Column('total_floors', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('total_students_capacity', sa.Integer(), nullable=False, server_default='200'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_hostels_code', 'hostels', ['code'], unique=True)

    # 2. Add hostel_id to users
    op.add_column('users', sa.Column('hostel_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_users_hostel_id', 'users', ['hostel_id'])
    op.create_foreign_key('fk_users_hostel_id', 'users', 'hostels', ['hostel_id'], ['id'], ondelete='SET NULL')

    # 3. Add hostel_id to complaints
    op.add_column('complaints', sa.Column('hostel_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_complaints_hostel_id', 'complaints', ['hostel_id'])
    op.create_foreign_key('fk_complaints_hostel_id', 'complaints', 'hostels', ['hostel_id'], ['id'], ondelete='SET NULL')

    # 4. Add hostel_id to machines
    op.add_column('machines', sa.Column('hostel_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_machines_hostel_id', 'machines', ['hostel_id'])
    op.create_foreign_key('fk_machines_hostel_id', 'machines', 'hostels', ['hostel_id'], ['id'], ondelete='SET NULL')

    # 5. Add hostel_id to laundry_slots
    op.add_column('laundry_slots', sa.Column('hostel_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_laundry_slots_hostel_id', 'laundry_slots', ['hostel_id'])
    op.create_foreign_key('fk_laundry_slots_hostel_id', 'laundry_slots', 'hostels', ['hostel_id'], ['id'], ondelete='SET NULL')

    # 6. Add hostel_id to mess_feedback
    op.add_column('mess_feedback', sa.Column('hostel_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_mess_feedback_hostel_id', 'mess_feedback', ['hostel_id'])
    op.create_foreign_key('fk_mess_feedback_hostel_id', 'mess_feedback', 'hostels', ['hostel_id'], ['id'], ondelete='SET NULL')

    # 7. Add hostel_id to mess_alerts
    op.add_column('mess_alerts', sa.Column('hostel_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_mess_alerts_hostel_id', 'mess_alerts', ['hostel_id'])
    op.create_foreign_key('fk_mess_alerts_hostel_id', 'mess_alerts', 'hostels', ['hostel_id'], ['id'], ondelete='SET NULL')

    # 8. Add hostel_id to hostel_config
    op.add_column('hostel_config', sa.Column('hostel_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_hostel_config_hostel_id', 'hostel_config', ['hostel_id'])
    op.create_foreign_key('fk_hostel_config_hostel_id', 'hostel_config', 'hostels', ['hostel_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Remove in reverse order

    op.drop_constraint('fk_hostel_config_hostel_id', 'hostel_config', type_='foreignkey')
    op.drop_index('ix_hostel_config_hostel_id', table_name='hostel_config')
    op.drop_column('hostel_config', 'hostel_id')

    op.drop_constraint('fk_mess_alerts_hostel_id', 'mess_alerts', type_='foreignkey')
    op.drop_index('ix_mess_alerts_hostel_id', table_name='mess_alerts')
    op.drop_column('mess_alerts', 'hostel_id')

    op.drop_constraint('fk_mess_feedback_hostel_id', 'mess_feedback', type_='foreignkey')
    op.drop_index('ix_mess_feedback_hostel_id', table_name='mess_feedback')
    op.drop_column('mess_feedback', 'hostel_id')

    op.drop_constraint('fk_laundry_slots_hostel_id', 'laundry_slots', type_='foreignkey')
    op.drop_index('ix_laundry_slots_hostel_id', table_name='laundry_slots')
    op.drop_column('laundry_slots', 'hostel_id')

    op.drop_constraint('fk_machines_hostel_id', 'machines', type_='foreignkey')
    op.drop_index('ix_machines_hostel_id', table_name='machines')
    op.drop_column('machines', 'hostel_id')

    op.drop_constraint('fk_complaints_hostel_id', 'complaints', type_='foreignkey')
    op.drop_index('ix_complaints_hostel_id', table_name='complaints')
    op.drop_column('complaints', 'hostel_id')

    op.drop_constraint('fk_users_hostel_id', 'users', type_='foreignkey')
    op.drop_index('ix_users_hostel_id', table_name='users')
    op.drop_column('users', 'hostel_id')

    op.drop_index('ix_hostels_code', table_name='hostels')
    op.drop_table('hostels')
