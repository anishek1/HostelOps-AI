"""
schemas/override_log.py — HostelOps AI
=========================================
Pydantic v2 schemas for the OverrideLog entity.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas.enums import ComplaintCategory, ComplaintSeverity, OverrideReason


class OverrideLogCreate(BaseModel):
    complaint_id: str
    warden_id: str
    original_category: ComplaintCategory
    corrected_category: ComplaintCategory
    original_severity: ComplaintSeverity
    corrected_severity: ComplaintSeverity
    original_assignee: str | None
    corrected_assignee: str | None
    reason: OverrideReason


class OverrideLogRead(OverrideLogCreate):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
