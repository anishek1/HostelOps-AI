"""
schemas/mess.py — HostelOps AI
==================================
Pydantic schemas for mess feedback and alerts (Sprint 4).
MessFeedback uses 5 dimension scores matching the existing DB model.
Sprint 7b: Added MessMenuCreate, MessMenuRead.
Field validators convert UUID → str per Golden Rule 17.
"""
import logging
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.enums import MealPeriod, MealType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mess Feedback schemas
# ---------------------------------------------------------------------------

class MessFeedbackCreate(BaseModel):
    """
    Student submits feedback for a meal.
    Each dimension is rated 1-5.
    Uses MealPeriod enum (breakfast/lunch/dinner) matching the existing DB model.
    """
    meal: MealPeriod
    feedback_date: date
    food_quality: int = Field(ge=1, le=5)
    food_quantity: int = Field(ge=1, le=5)
    hygiene: int = Field(ge=1, le=5)
    menu_variety: int = Field(ge=1, le=5)
    timing: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class MessFeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    meal: MealPeriod
    feedback_date: date = Field(alias="date")
    food_quality: int
    food_quantity: int
    hygiene: int
    menu_variety: int
    timing: int
    comment: Optional[str] = None
    created_at: datetime
    avg_rating: Optional[float] = None  # computed field

    @field_validator("id", "student_id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        return str(v) if v is not None else None


class MessAlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    alert_type: str
    dimension: str
    meal: MealPeriod
    average_score: float
    participation_count: int
    resolved: bool
    triggered_at: datetime
    resolved_at: Optional[datetime] = None

    @field_validator("id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        return str(v) if v is not None else None


class MessSummaryResponse(BaseModel):
    """Aggregated summary of feedback for a date/meal."""
    feedback_date: date
    meal: Optional[MealPeriod] = None
    avg_food_quality: float
    avg_food_quantity: float
    avg_hygiene: float
    avg_menu_variety: float
    avg_timing: float
    overall_avg: float
    participation_count: int
    trend: str  # "improving", "declining", "stable"


# ---------------------------------------------------------------------------
# Sprint 7b: Mess Menu schemas
# ---------------------------------------------------------------------------

class MessMenuCreate(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    meal: MealType
    items: List[str] = Field(..., min_length=1)
    valid_from: date


class MessMenuRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    hostel_id: Optional[str] = None
    day_of_week: int
    meal: MealType
    items: List[str]
    valid_from: date
    created_by: str
    created_at: datetime

    @field_validator("id", "hostel_id", "created_by", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        return str(v) if v is not None else None
