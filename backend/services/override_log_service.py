"""
override_log_service.py — HostelOps AI
========================================
Service for creating override log entries.
Called by log_override_tool — never called directly from routes.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from models.override_log import OverrideLog
from schemas.enums import ComplaintCategory, ComplaintSeverity, OverrideReason
import uuid

async def create_override_log(
    complaint_id: str,
    warden_id: str,
    original_category: ComplaintCategory,
    corrected_category: ComplaintCategory,
    original_severity: ComplaintSeverity,
    corrected_severity: ComplaintSeverity,
    original_assignee: str | None,
    corrected_assignee: str | None,
    reason: OverrideReason,
    db: AsyncSession
) -> OverrideLog:
    """
    Creates an override log entry in the database.
    Called exclusively by log_override_tool.
    """
    log = OverrideLog(
        id=uuid.uuid4(),
        complaint_id=uuid.UUID(complaint_id),
        warden_id=uuid.UUID(warden_id),
        original_category=original_category,
        corrected_category=corrected_category,
        original_severity=original_severity,
        corrected_severity=corrected_severity,
        original_assignee=uuid.UUID(original_assignee) if original_assignee else None,
        corrected_assignee=uuid.UUID(corrected_assignee) if corrected_assignee else None,
        reason=reason,
    )
    db.add(log)
    await db.flush()
    return log
