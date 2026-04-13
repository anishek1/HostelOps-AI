"""simplify roles to 3: student, laundry_man, mess_staff, warden

Revision ID: f1a2b3c4d5e6
Revises: ec3264ca7257
Create Date: 2026-04-03

Adds mess_staff enum value and migrates existing users:
- mess_secretary + mess_manager -> mess_staff
- assistant_warden + chief_warden -> warden

Note: PostgreSQL does not allow removing enum values without recreating the type.
Old values (mess_secretary, mess_manager, assistant_warden, chief_warden) remain
in the DB enum type but are no longer used in application code.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'ec3264ca7257'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ADD VALUE cannot be used in the same transaction as DML that
    # references the new value. autocommit_block() commits the current Alembic
    # transaction, runs the statement in autocommit mode, then resumes.
    with op.get_context().autocommit_block():
        op.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'mess_staff'"))

    # Now that 'mess_staff' is committed, migrate existing users to new roles
    op.execute(sa.text("""
        UPDATE users
        SET role = 'mess_staff'
        WHERE role IN ('mess_secretary', 'mess_manager')
    """))
    op.execute(sa.text("""
        UPDATE users
        SET role = 'warden'
        WHERE role IN ('assistant_warden', 'chief_warden')
    """))


def downgrade() -> None:
    # Revert role migrations (enum value removal not supported in PostgreSQL)
    op.execute("""
        UPDATE users
        SET role = 'mess_secretary'
        WHERE role = 'mess_staff'
    """)
    op.execute("""
        UPDATE users
        SET role = 'assistant_warden'
        WHERE role = 'warden'
    """)
