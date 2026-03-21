"""
models/hostel_config.py — HostelOps AI
========================================
SQLAlchemy ORM model for the HostelConfig entity.
Single row per deployment — stores per-hostel operational thresholds.
Overrides .env defaults when a DB row exists.
Sprint 5: Added to allow wardens to configure thresholds from UI.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class HostelConfig(Base):
    __tablename__ = "hostel_config"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    # Sprint 7: Multi-tenant — one config row per hostel
    hostel_id = Column(UUID(as_uuid=True), ForeignKey("hostels.id", ondelete="CASCADE"), nullable=True, index=True)
    hostel_name = Column(String(255), nullable=False, default="Hostel")
    hostel_mode = Column(String(50), nullable=False, default="college")  # "college" | "autonomous"
    total_floors = Column(Integer, nullable=False, default=3)
    total_students_capacity = Column(Integer, nullable=False, default=200)

    # Complaint thresholds
    complaint_rate_limit = Column(Integer, nullable=False, default=5)
    approval_queue_timeout_minutes = Column(Integer, nullable=False, default=30)
    complaint_confidence_threshold = Column(Float, nullable=False, default=0.85)

    # Mess thresholds
    mess_alert_threshold = Column(Float, nullable=False, default=2.5)
    mess_critical_threshold = Column(Float, nullable=False, default=2.0)
    mess_min_participation = Column(Float, nullable=False, default=0.15)
    mess_min_responses = Column(Integer, nullable=False, default=5)

    # Laundry thresholds
    laundry_slots_start_hour = Column(Integer, nullable=False, default=8)
    laundry_slots_end_hour = Column(Integer, nullable=False, default=22)
    laundry_slot_duration_hours = Column(Integer, nullable=False, default=1)
    laundry_noshow_penalty_hours = Column(Integer, nullable=False, default=48)
    laundry_cancellation_deadline_minutes = Column(Integer, nullable=False, default=15)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
