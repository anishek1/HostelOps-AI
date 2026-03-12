"""
schemas/complaint.py — HostelOps AI
======================================
Pydantic v2 schemas for the Complaint entity.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.enums import (
    ClassifiedBy,
    ComplaintCategory,
    ComplaintSeverity,
    ComplaintStatus,
    OverrideReason,
)


class ComplaintCreate(BaseModel):
    text: str = Field(..., max_length=1000)
    is_anonymous: bool = False


class ComplaintRead(BaseModel):
    id: str
    student_id: str
    text: str
    is_anonymous: bool
    category: ComplaintCategory | None
    severity: ComplaintSeverity | None
    status: ComplaintStatus
    assigned_to: str | None
    confidence_score: float | None
    ai_suggested_category: ComplaintCategory | None
    ai_suggested_assignee: str | None
    requires_approval: bool
    classified_by: ClassifiedBy
    override_reason: OverrideReason | None
    flagged_input: str | None
    resolved_confirmed_at: datetime | None = None
    reopen_reason: str | None = None
    is_priority: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplaintReadAnonymous(BaseModel):
    """Safe schema for anonymous complaints — omits student_id."""
    id: str
    text: str
    is_anonymous: bool
    category: ComplaintCategory | None
    severity: ComplaintSeverity | None
    status: ComplaintStatus
    assigned_to: str | None
    confidence_score: float | None
    requires_approval: bool
    classified_by: ClassifiedBy
    resolved_confirmed_at: datetime | None = None
    reopen_reason: str | None = None
    is_priority: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplaintUpdate(BaseModel):
    status: ComplaintStatus | None = None
    assigned_to: str | None = None
    override_reason: OverrideReason | None = None

    model_config = ConfigDict(from_attributes=True)


class ClassificationResult(BaseModel):
    """Returned by the LLM classification agent or fallback classifier."""
    category: ComplaintCategory
    severity: ComplaintSeverity
    classified_by: ClassifiedBy
    confidence_score: float = 0.0
    requires_approval: bool = False
    note: str | None = None
    suggested_assignee_role: str | None = None
