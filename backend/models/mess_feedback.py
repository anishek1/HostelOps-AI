from __future__ import annotations
"""
models/mess_feedback.py — HostelOps AI
==========================================
SQLAlchemy ORM model for the MessFeedback entity.
Feedback ratings stored as flat int columns (not nested JSON) for queryability.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base
from schemas.enums import MealPeriod


class MessFeedback(Base):
    __tablename__ = "mess_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    meal: Mapped[MealPeriod] = mapped_column(
        Enum(MealPeriod, name="mealperiod"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    food_quality: Mapped[int] = mapped_column(Integer, nullable=False)
    food_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    hygiene: Mapped[int] = mapped_column(Integer, nullable=False)
    menu_variety: Mapped[int] = mapped_column(Integer, nullable=False)
    timing: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
