"""
models/approval_queue.py — HostelOps AI
==========================================
SQLAlchemy ORM model for the ApprovalQueueItem entity.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base
from schemas.enums import ApprovalStatus, ComplaintCategory, ComplaintSeverity


class ApprovalQueueItem(Base):
    __tablename__ = "approval_queue"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False
    )
    ai_suggested_category: Mapped[ComplaintCategory] = mapped_column(
        Enum(ComplaintCategory, name="complaintcategory"), nullable=False
    )
    ai_suggested_severity: Mapped[ComplaintSeverity] = mapped_column(
        Enum(ComplaintSeverity, name="complaintseverity"), nullable=False
    )
    ai_suggested_assignee: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approvalstatus"),
        default=ApprovalStatus.pending,
        nullable=False,
    )
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    override_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
