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
    return notification
    



async def notify_all_by_role(
    role,
    title: str,
    body: str,
    notification_type: NotificationType,
    db: AsyncSession,
    hostel_id=None,
) -> int:
    """
    Send the same notification to all users with a specific role.
    Sprint 7: Scoped to hostel_id when provided — never notifies across hostels.
    Returns the count of notifications created.
    """
    from sqlalchemy import select
    from models.user import User

    query = select(User).where(User.role == role, User.is_active == True)  # noqa: E712
    if hostel_id is not None:
        query = query.where(User.hostel_id == hostel_id)

    result = await db.execute(query)
    users = result.scalars().all()

    for user in users:
        await notify_user(user.id, title, body, notification_type, db)

    return len(users)
