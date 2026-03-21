from __future__ import annotations
"""
models/mess_alert.py — HostelOps AI
=======================================
SQLAlchemy ORM model for the MessAlert entity.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base
from schemas.enums import AlertType, MealPeriod, MessDimension


class MessAlert(Base):
    __tablename__ = "mess_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, name="alerttype"), nullable=False
    )
    dimension: Mapped[MessDimension] = mapped_column(
        Enum(MessDimension, name="messdimension"), nullable=False
    )
    meal: Mapped[MealPeriod] = mapped_column(
        Enum(MealPeriod, name="mealperiod"), nullable=False
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    average_score: Mapped[float] = mapped_column(Float, nullable=False)
    participation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Sprint 7: Multi-tenant
    hostel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hostels.id", ondelete="SET NULL"), nullable=True, index=True
    )
