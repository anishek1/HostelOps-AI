"""
routes/analytics.py — HostelOps AI
=====================================
Analytics and evaluation metrics routes.
Warden-level access only for main dashboard.
Sprint 5: New route file.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from schemas.enums import UserRole
from schemas.metrics import (
    ComplaintsAnalytics,
    DashboardMetrics,
    LaundryAnalytics,
    MessAnalytics,
)
from services import metrics_service
from services.auth_service import require_role

logger = logging.getLogger(__name__)

router = APIRouter()

_WARDEN_ROLES = (UserRole.warden,)


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    days: int = Query(30, ge=1, le=90, description="Rolling window in days"),
    current_user: User = Depends(require_role(*_WARDEN_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """
    Return all evaluation metrics for the specified period.
    Includes drift alert if misclassification rate exceeds 25%.
    """
    metrics = await metrics_service.get_full_dashboard_metrics(days, db, hostel_id=current_user.hostel_id)
    logger.info(f"Dashboard metrics rendered for {current_user.role.value} — drift_alert={metrics.drift_alert}")
    return metrics


@router.get("/complaints", response_model=ComplaintsAnalytics)
async def get_complaints_analytics(
    days: int = Query(30, ge=1, le=90),
    category: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_role(*_WARDEN_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Complaint breakdown analytics."""
    return await metrics_service.get_complaints_analytics(days, category, status, db, hostel_id=current_user.hostel_id)


@router.get("/mess", response_model=MessAnalytics)
async def get_mess_analytics(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(
        require_role(UserRole.warden, UserRole.mess_staff)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Mess feedback trend analytics."""
    return await metrics_service.get_mess_analytics(days, db, hostel_id=current_user.hostel_id)


@router.get("/laundry", response_model=LaundryAnalytics)
async def get_laundry_analytics(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(
        require_role(UserRole.warden, UserRole.laundry_man)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Laundry slot utilization analytics."""
    return await metrics_service.get_laundry_analytics(days, db, hostel_id=current_user.hostel_id)


@router.get("/overrides")
async def get_override_logs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(UserRole.warden)),
    db: AsyncSession = Depends(get_db),
):
    """Recent AI override log entries."""
    logs = await metrics_service.get_override_logs(
        db, limit=limit, offset=offset, hostel_id=current_user.hostel_id
    )
    return {
        "total": len(logs),
        "items": [
            {
                "id": str(log.id),
                "complaint_id": str(log.complaint_id),
                "corrected_by": str(log.warden_id),
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }
