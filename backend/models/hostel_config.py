"""
models/hostel_config.py — HostelOps AI
========================================
SQLAlchemy ORM model for the HostelConfig entity.
Single row per hostel — stores per-hostel operational thresholds.
Overrides .env defaults when a DB row exists.
Sprint 5: Added to allow wardens to configure thresholds from UI.
Sprint 7: Multi-tenant (one row per hostel). Fix 16: migrated to mapped_column().
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base


class HostelConfig(Base):
    __tablename__ = "hostel_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Sprint 7: Multi-tenant — one config row per hostel
    hostel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hostels.id", ondelete="CASCADE"), nullable=True, index=True
    )
    hostel_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Hostel")
    hostel_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="college")

    total_floors: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    total_students_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=200)

    # Complaint thresholds
    complaint_rate_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    approval_queue_timeout_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    complaint_confidence_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.85)

    # Mess thresholds
    mess_alert_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    mess_critical_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    mess_min_participation: Mapped[float] = mapped_column(Float, nullable=False, default=0.15)
    mess_min_responses: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # Laundry thresholds
    laundry_slots_start_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    laundry_slots_end_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=22)
    laundry_slot_duration_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    laundry_noshow_penalty_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=48)
    laundry_cancellation_deadline_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
