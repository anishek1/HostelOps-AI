from __future__ import annotations
"""
models/__init__.py — HostelOps AI
====================================
Imports all models so Alembic can detect them for autogenerate migrations.
NEVER remove any import from this file.
"""

from models.user import User                        # noqa: F401
from models.complaint import Complaint              # noqa: F401
from models.machine import Machine                  # noqa: F401
from models.laundry_slot import LaundrySlot         # noqa: F401
from models.mess_feedback import MessFeedback       # noqa: F401
from models.mess_alert import MessAlert             # noqa: F401
from models.approval_queue import ApprovalQueueItem # noqa: F401
from models.override_log import OverrideLog         # noqa: F401
from models.audit_log import AuditLog               # noqa: F401
from models.notification import Notification        # noqa: F401
