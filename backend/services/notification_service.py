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
    """
    notification = Notification(
        recipient_id=recipient_id,
        title=title,
        body=body,
        type=notification_type,
        is_read=False
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    
    # Fire push notification (fire and forget)
    from services.push_service import send_push_notification
    try:
        await send_push_notification(
            user_id=str(recipient_id),
            title=title,
            body=body,
            data={"type": notification_type.value},
            db=db
        )
    except Exception as e:
        logger.warning(f"[notify_user] Push notification failed for {recipient_id}: {e}")
    
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
