"""
services/notification_service.py — HostelOps AI
=================================================
Handles writing notifications to the in-app inbox.
Push delivery (pywebpush) is a future enhancement — in-app DB record is the reliable fallback.
Service functions called from routes. Never call directly from agents or tasks yet.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.notification import Notification
from schemas.enums import NotificationType


async def notify_user(
    recipient_id: uuid.UUID,
    title: str,
    body: str,
    notification_type: NotificationType,
    db: AsyncSession,
) -> Notification:
    """
    Write a notification record to the database.
    Always succeeds — push delivery is separate and best-effort.
    """
    notification = Notification(
        recipient_id=recipient_id,
        title=title,
        body=body,
        type=notification_type,
    )
    db.add(notification)
    # Caller is responsible for committing the session
    return notification


async def notify_all_by_role(
    role,
    title: str,
    body: str,
    notification_type: NotificationType,
    db: AsyncSession,
) -> int:
    """
    Send the same notification to all users with a specific role.
    Returns the count of notifications created.
    """
    from sqlalchemy import select
    from models.user import User

    result = await db.execute(
        select(User).where(User.role == role, User.is_active == True)  # noqa: E712
    )
    users = result.scalars().all()

    for user in users:
        await notify_user(user.id, title, body, notification_type, db)

    return len(users)
