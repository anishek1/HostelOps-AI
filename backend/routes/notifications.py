"""
routes/notifications.py — HostelOps AI
=========================================
Notification inbox endpoints — read, mark-read, mark-all-read.
Routes are thin — minimal logic, direct DB operations.
"""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from models.notification import Notification
from models.user import User
from schemas.notification import NotificationRead
from services.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /api/notifications/ — user's notifications
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=List[NotificationRead],
    summary="Get current user's notifications",
)
async def get_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.recipient_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    notifications = result.scalars().all()
    return [
        NotificationRead(
            id=str(n.id),
            recipient_id=str(n.recipient_id),
            title=n.title,
            body=n.body,
            type=n.type,
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n in notifications
    ]


# ---------------------------------------------------------------------------
# PATCH /api/notifications/{notification_id}/read — mark as read
# ---------------------------------------------------------------------------


@router.patch(
    "/{notification_id}/read",
    summary="Mark a notification as read",
)
async def mark_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notification = await db.get(Notification, uuid.UUID(notification_id))
    if not notification or notification.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = True
    db.add(notification)
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# PATCH /api/notifications/read-all — mark all as read
# ---------------------------------------------------------------------------


@router.patch(
    "/read-all",
    summary="Mark all notifications as read",
)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        update(Notification)
        .where(Notification.recipient_id == current_user.id)
        .values(is_read=True)
    )
    await db.execute(stmt)
    return {"status": "ok"}
