"""
tools/mess_tools.py — HostelOps AI
=====================================
Agent 3 tool callables. Async wrappers around mess_service.
"""
import logging
import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from services import mess_service
from schemas.enums import MealPeriod

logger = logging.getLogger(__name__)


class SubmitFeedbackInput(BaseModel):
    student_id: str
    meal: str  # breakfast / lunch / dinner
    feedback_date: str  # YYYY-MM-DD
    food_quality: int
    food_quantity: int
    hygiene: int
    menu_variety: int
    timing: int
    comment: Optional[str] = None


async def submit_feedback_tool(input: SubmitFeedbackInput, db: AsyncSession):
    """Submits 5-dimension mess feedback for a student."""
    feedback = await mess_service.submit_feedback(
        student_id=uuid.UUID(input.student_id),
        meal=MealPeriod(input.meal),
        feedback_date=date.fromisoformat(input.feedback_date),
        food_quality=input.food_quality,
        food_quantity=input.food_quantity,
        hygiene=input.hygiene,
        menu_variety=input.menu_variety,
        timing=input.timing,
        comment=input.comment,
        db=db,
    )
    return {"status": "success", "feedback_id": str(feedback.id)}


class GetFeedbackSummaryInput(BaseModel):
    feedback_date: str  # YYYY-MM-DD
    meal: Optional[str] = None  # breakfast / lunch / dinner / None for all


async def get_feedback_summary_tool(input: GetFeedbackSummaryInput, db: AsyncSession):
    """Returns the daily mess feedback summary with trend."""
    meal = MealPeriod(input.meal) if input.meal else None
    summary = await mess_service.get_daily_summary(
        feedback_date=date.fromisoformat(input.feedback_date),
        meal=meal,
        db=db,
    )
    return summary.model_dump()


class SendMessAlertInput(BaseModel):
    feedback_date: str  # YYYY-MM-DD — date to check and alert for


async def send_mess_alert_tool(input: SendMessAlertInput, db: AsyncSession):
    """Triggers threshold check and sends alerts for a specific date."""
    await mess_service.check_and_alert(
        feedback_date=date.fromisoformat(input.feedback_date),
        db=db,
    )
    return {"status": "alert_check_complete"}
