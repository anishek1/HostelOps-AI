from __future__ import annotations
"""
models/user.py — HostelOps AI
================================
SQLAlchemy ORM model for the User entity.
Sprint 6: Added is_rejected, rejection_reason, has_seen_onboarding columns.
Sprint 7b: Added feedback_streak, last_feedback_date columns.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base
from schemas.enums import HostelMode, UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    room_number: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"), nullable=False
    )
    hostel_mode: Mapped[HostelMode] = mapped_column(
        Enum(HostelMode, name="hostelmode"), nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    roll_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    erp_document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Sprint 6: Registration rejection flow
    is_rejected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    # Sprint 6: Onboarding flag
    has_seen_onboarding: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Sprint 7: Multi-tenant
    hostel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hostels.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Sprint 7b: Feedback streak
    feedback_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_feedback_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
