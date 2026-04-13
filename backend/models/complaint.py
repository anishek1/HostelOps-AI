"""
models/complaint.py — HostelOps AI
=====================================
SQLAlchemy ORM model for the Complaint entity.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None
from sqlalchemy.types import VARCHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base
from schemas.enums import (
    ClassifiedBy,
    ComplaintCategory,
    ComplaintSeverity,
    ComplaintStatus,
    OverrideReason,
)


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    sanitized_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    category: Mapped[Optional[ComplaintCategory]] = mapped_column(
        Enum(ComplaintCategory, name="complaintcategory"), nullable=True
    )
    severity: Mapped[Optional[ComplaintSeverity]] = mapped_column(
        Enum(ComplaintSeverity, name="complaintseverity"), nullable=True
    )
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, name="complaintstatus"),
        default=ComplaintStatus.INTAKE,
        nullable=False,
    )
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # LLM extraction fields (Phase 2)
    urgency: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    affected_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    safety_flag: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    language_detected: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Kept for backwards compatibility — no longer used for routing decisions
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_suggested_category: Mapped[Optional[ComplaintCategory]] = mapped_column(
        Enum(ComplaintCategory, name="complaintcategory"), nullable=True
    )
    ai_suggested_assignee: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    classified_by: Mapped[ClassifiedBy] = mapped_column(
        Enum(ClassifiedBy, name="classifiedby"),
        default=ClassifiedBy.fallback,
        nullable=False,
    )
    flagged_input: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Feedback loop: warden's corrected category, stored for AI accuracy analytics
    warden_corrected_category: Mapped[Optional[ComplaintCategory]] = mapped_column(
        Enum(ComplaintCategory, name="complaintcategory"), nullable=True
    )
    override_reason: Mapped[Optional[OverrideReason]] = mapped_column(
        Enum(OverrideReason, name="overridereason"), nullable=True
    )
    resolved_confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reopen_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_priority: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Phase 5: Semantic deduplication (pgvector)
    embedding = mapped_column(Vector(384), nullable=True) if Vector else None
    # Sprint 7: Multi-tenant
    hostel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hostels.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
