"""
schemas/approval_queue.py — HostelOps AI
==========================================
Pydantic v2 schemas for the ApprovalQueueItem entity.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas.enums import ApprovalStatus, ComplaintCategory, ComplaintSeverity


class ApprovalQueueItemCreate(BaseModel):
    complaint_id: str
    ai_suggested_category: ComplaintCategory
    ai_suggested_severity: ComplaintSeverity
    ai_suggested_assignee: str
    confidence_score: float


class ApprovalQueueItemRead(BaseModel):
    id: str
    complaint_id: str
    ai_suggested_category: ComplaintCategory
    ai_suggested_severity: ComplaintSeverity
    ai_suggested_assignee: str
    confidence_score: float
    status: ApprovalStatus
    reviewed_by: str | None
    override_reason: str | None
    created_at: datetime
    reviewed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
