from __future__ import annotations
"""
models/machine.py — HostelOps AI
====================================
SQLAlchemy ORM model for the Machine entity.
Sprint 4: Added floor and status columns.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base
from schemas.enums import MachineStatus


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    floor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[MachineStatus] = mapped_column(
        Enum(MachineStatus, name="machinestatus"),
        default=MachineStatus.operational,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_reported_issue: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    repaired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
