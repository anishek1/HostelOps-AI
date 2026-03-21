from __future__ import annotations
"""
models/hostel.py — HostelOps AI
==================================
SQLAlchemy ORM model for the Hostel entity.
Sprint 7: Multi-tenant architecture. One row per hostel.
Each hostel has a unique human-readable code (e.g. IGBH-4821) shared with students.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base
from schemas.enums import HostelMode


class Hostel(Base):
    __tablename__ = "hostels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    mode: Mapped[HostelMode] = mapped_column(
        Enum(HostelMode, name="hostelmode"), nullable=False
    )
    total_floors: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    total_students_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
