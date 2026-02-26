"""
schemas/mess_feedback.py — HostelOps AI
==========================================
Pydantic v2 schemas for the MessFeedback entity.
Rating dimensions: 1–5 integers.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.enums import MealPeriod


class MessRatings(BaseModel):
    food_quality: int = Field(..., ge=1, le=5)
    food_quantity: int = Field(..., ge=1, le=5)
    hygiene: int = Field(..., ge=1, le=5)
    menu_variety: int = Field(..., ge=1, le=5)
    timing: int = Field(..., ge=1, le=5)


class MessFeedbackCreate(BaseModel):
    meal: MealPeriod
    date: date
    ratings: MessRatings
    comment: str | None = Field(default=None, max_length=300)


class MessFeedbackRead(BaseModel):
    id: str
    student_id: str
    meal: MealPeriod
    date: date
    food_quality: int
    food_quantity: int
    hygiene: int
    menu_variety: int
    timing: int
    comment: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
