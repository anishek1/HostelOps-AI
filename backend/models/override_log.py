"""
models/override_log.py — HostelOps AI
========================================
SQLAlchemy ORM model for the OverrideLog entity.
Immutable audit trail — no updated_at.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base
from schemas.enums import ComplaintCategory, ComplaintSeverity, OverrideReason


class OverrideLog(Base):
    __tablename__ = "override_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False
    )
    warden_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    original_category: Mapped[ComplaintCategory] = mapped_column(
        Enum(ComplaintCategory, name="complaintcategory"), nullable=False
    )
    corrected_category: Mapped[ComplaintCategory] = mapped_column(
        Enum(ComplaintCategory, name="complaintcategory"), nullable=False
    )
    original_severity: Mapped[ComplaintSeverity] = mapped_column(
        Enum(ComplaintSeverity, name="complaintseverity"), nullable=False
    )
    corrected_severity: Mapped[ComplaintSeverity] = mapped_column(
        Enum(ComplaintSeverity, name="complaintseverity"), nullable=False
    )
    original_assignee: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    corrected_assignee: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[OverrideReason] = mapped_column(
        Enum(OverrideReason, name="overridereason"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
