from __future__ import annotations
"""
models/laundry_slot.py — HostelOps AI
========================================
SQLAlchemy ORM model for the LaundrySlot entity.
Sprint 4: Added slot_date, slot_time, priority_score, booked_at, completed_at.
LaundrySlotStatus controls the booking lifecycle (available/booked/completed/cancelled).
"""
import uuid
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base
from schemas.enums import LaundrySlotStatus, SlotStatus


class LaundrySlot(Base):
    __tablename__ = "laundry_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    machine_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    # Sprint 1 legacy columns — kept as-is
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    is_priority: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    priority_approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Sprint 4 additions
    slot_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    slot_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # e.g. "08:00-09:00"
    booking_status: Mapped[LaundrySlotStatus] = mapped_column(
        Enum(LaundrySlotStatus, name="laundryslostatus"),
        default=LaundrySlotStatus.available,
        nullable=False,
    )
    priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    booked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Sprint 5: No-show and late cancellation tracking
    no_show_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    late_cancellation_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
