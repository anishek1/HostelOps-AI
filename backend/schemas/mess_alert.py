"""
schemas/mess_alert.py — HostelOps AI
=======================================
Pydantic v2 schemas for the MessAlert entity.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas.enums import AlertType, MealPeriod, MessDimension


class MessAlertRead(BaseModel):
    id: str
    alert_type: AlertType
    dimension: MessDimension
    meal: MealPeriod
    triggered_at: datetime
    average_score: float
    participation_count: int
    resolved: bool
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
