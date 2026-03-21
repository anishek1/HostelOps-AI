"""
models/mess_menu.py — HostelOps AI
======================================
SQLAlchemy ORM model for the MessMenu entity.
Sprint 7b: Mess menu per hostel, per day_of_week, per meal.
items stored as JSONB array of strings.
"""
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base
from schemas.enums import MealType


class MessMenu(Base):
    __tablename__ = "mess_menu"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hostel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hostels.id", ondelete="CASCADE"), nullable=True, index=True
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon, 6=Sun
    meal: Mapped[MealType] = mapped_column(
        Enum(MealType, name="mealtype", create_type=False), nullable=False
    )
    items: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
