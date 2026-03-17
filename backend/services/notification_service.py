"""
services/notification_service.py — HostelOps AI
=================================================
Handles writing notifications to the in-app inbox.
Sprint 5: After writing to DB, fires a best-effort push notification.
Push failures are swallowed — they must never affect in-app notification delivery.
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.notification import Notification
from schemas.enums import NotificationType

logger = logging.getLogger(__name__)


async def notify_user(
    recipient_id: uuid.UUID,
    title: str,
    body: str,
    notification_type: NotificationType,
    db: AsyncSession,
) -> Notification:
    """
    Write a notification record to the database.
    After commit, fires a best-effort push notification.
    The caller is responsible for the outer commit — push fires AFTER.
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


async def notify_user_with_push(
    recipient_id: uuid.UUID,
    title: str,
    body: str,
    notification_type: NotificationType,
    db: AsyncSession,
) -> Notification:
    """
    Write a notification record AND send a best-effort push notification.
    Use this variant when the caller wants auto-push delivery.
    Commits the notification, then tries push (push failures are logged only).
    """
    from services.push_service import send_push_notification

    notification = Notification(
        recipient_id=recipient_id,
        title=title,
        body=body,
        type=notification_type,
    )
    db.add(notification)
    # Commit the in-app notification first — push must never block this
    await db.commit()
    await db.refresh(notification)

    # Best-effort push — swallow all errors
    try:
        await send_push_notification(
            user_id=str(recipient_id),
            title=title,
            body=body,
            db=db,
        )
    except Exception as e:
        logger.error(f"Push notification failed for user {recipient_id}: {e}")

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
