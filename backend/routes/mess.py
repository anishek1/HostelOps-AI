"""
routes/mess.py — HostelOps AI
==================================
Mess feedback submission and reporting endpoints.
Thin routes — all logic in services/mess_service.py.
"""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List, Optional

from database import get_db
from models.user import User
from schemas.mess import MessFeedbackCreate, MessFeedbackRead, MessSummaryResponse, MessAlertRead
from schemas.enums import MealPeriod, UserRole
from services.auth_service import get_current_user, require_role
from services import mess_service

logger = logging.getLogger(__name__)

router = APIRouter()

WARDEN_ROLES = [UserRole.assistant_warden, UserRole.warden, UserRole.chief_warden]


# ---------------------------------------------------------------------------
# Feedback Routes
# ---------------------------------------------------------------------------

@router.post("/feedback")
async def submit_feedback(
    feedback: MessFeedbackCreate,
    current_user: User = Depends(require_role(UserRole.student)),
    db: AsyncSession = Depends(get_db),
):
    """Submit mess feedback for a meal (students only)."""
    try:
        fb = await mess_service.submit_feedback(
            student_id=current_user.id,
            meal=feedback.meal,
            feedback_date=feedback.feedback_date,
            food_quality=feedback.food_quality,
            food_quantity=feedback.food_quantity,
            hygiene=feedback.hygiene,
            menu_variety=feedback.menu_variety,
            timing=feedback.timing,
            comment=feedback.comment,
            db=db,
        )
        return {"message": "Feedback submitted", "id": str(fb.id)}
    except ValueError as e:
        if "already submitted" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary", response_model=MessSummaryResponse)
async def get_summary(
    feedback_date: date = Query(..., description="Date in YYYY-MM-DD format"),
    meal: Optional[MealPeriod] = Query(None, description="Filter by meal period"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get feedback summary for a specific date and optional meal."""
    summary = await mess_service.get_daily_summary(feedback_date, meal, db)
    return summary


@router.get("/alerts", response_model=List[MessAlertRead])
async def get_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent mess alerts (warden + mess_manager only)."""
    allowed = WARDEN_ROLES + [UserRole.mess_manager]
    if current_user.role not in allowed:
        raise HTTPException(status_code=403, detail="Access restricted to wardens and mess managers")
    alerts = await mess_service.get_recent_alerts(db)
    return [MessAlertRead.model_validate(a) for a in alerts]


@router.get("/my-feedback", response_model=List[MessFeedbackRead])
async def my_feedback(
    current_user: User = Depends(require_role(UserRole.student)),
    db: AsyncSession = Depends(get_db),
):
    """Get the current student's feedback history (last 30 days)."""
    feedbacks = await mess_service.get_student_feedback(current_user.id, db)
    return [MessFeedbackRead.model_validate(f) for f in feedbacks]
