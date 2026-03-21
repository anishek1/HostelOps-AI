"""
routes/mess.py — HostelOps AI
==================================
Mess feedback submission and reporting endpoints.
Thin routes — all logic in services/mess_service.py and mess_menu_service.py.
Sprint 7b: Added mess menu endpoints and pagination.
"""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List, Optional

from database import get_db
from models.user import User
from schemas.mess import MessFeedbackCreate, MessFeedbackRead, MessMenuCreate, MessMenuRead, MessSummaryResponse, MessAlertRead
from schemas.enums import MealPeriod, UserRole
from services.auth_service import get_current_user, require_role
from services import mess_service
from services import mess_menu_service

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
            hostel_id=current_user.hostel_id,
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
    summary = await mess_service.get_daily_summary(feedback_date, meal, db, hostel_id=current_user.hostel_id)
    return summary


@router.get("/alerts", response_model=List[MessAlertRead])
async def get_alerts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent mess alerts (warden + mess_manager only)."""
    allowed = WARDEN_ROLES + [UserRole.mess_manager]
    if current_user.role not in allowed:
        raise HTTPException(status_code=403, detail="Access restricted to wardens and mess managers")
    alerts = await mess_service.get_recent_alerts(db, hostel_id=current_user.hostel_id)
    return [MessAlertRead.model_validate(a) for a in alerts[offset:offset + limit]]


@router.get("/my-feedback", response_model=List[MessFeedbackRead])
async def my_feedback(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(UserRole.student)),
    db: AsyncSession = Depends(get_db),
):
    """Get the current student's feedback history (last 30 days)."""
    feedbacks = await mess_service.get_student_feedback(current_user.id, db)
    return [MessFeedbackRead.model_validate(f) for f in feedbacks[offset:offset + limit]]


# ---------------------------------------------------------------------------
# Sprint 7b: Mess Menu endpoints
# ---------------------------------------------------------------------------


@router.post("/menu", response_model=MessMenuRead, status_code=201)
async def create_mess_menu(
    payload: MessMenuCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a mess menu entry. Allowed: mess_manager or WARDEN_ROLES."""
    allowed = WARDEN_ROLES + [UserRole.mess_manager]
    if current_user.role not in allowed:
        raise HTTPException(status_code=403, detail="Only mess managers and wardens can create menu entries.")
    menu = await mess_menu_service.create_menu(
        payload=payload,
        created_by=current_user.id,
        hostel_id=current_user.hostel_id,
        db=db,
    )
    return MessMenuRead.model_validate(menu)


@router.get("/menu", response_model=List[MessMenuRead])
async def get_mess_menu(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current mess menu for the hostel. Any authenticated user."""
    menus = await mess_menu_service.get_current_menu(
        hostel_id=current_user.hostel_id,
        db=db,
        limit=limit,
        offset=offset,
    )
    return [MessMenuRead.model_validate(m) for m in menus]
