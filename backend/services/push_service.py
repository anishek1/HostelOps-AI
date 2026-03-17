"""
services/push_service.py — HostelOps AI
=========================================
Web Push delivery service using pywebpush.
Sends push notifications to all registered browser subscriptions for a user.
Failed pushes are logged. 410 responses (expired subscription) are auto-removed.
Sprint 5: New service.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


async def send_push_notification(
    user_id: str,
    title: str,
    body: str,
    db: AsyncSession,
    data: Optional[dict] = None,
) -> None:
    """
    Send a push notification to all active subscriptions for a user.
    Best-effort: failures are logged but never raise.
    Called AFTER in-app notification commit so failures can't break the primary flow.
    """
    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        logger.debug("VAPID keys not configured — skipping push notification")
        return

    result = await db.execute(
        select(PushSubscription).where(PushSubscription.user_id == user_id)
    )
    subs = result.scalars().all()

    if not subs:
        return

    payload = json.dumps({
        "title": title,
        "body": body,
        "data": data or {},
        "icon": "/icon-192.png",
        "badge": "/badge-72.png",
    })

    endpoints_to_remove = []

    for sub in subs:
        try:
            from pywebpush import WebPushException, webpush
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.VAPID_CLAIM_EMAIL}"},
            )
            # Update last_used_at
            sub.last_used_at = datetime.now(timezone.utc)
            db.add(sub)
            logger.debug(f"Push sent to subscription {sub.id} for user {user_id}")

        except Exception as exc:
            # Check if it's a 410 Gone (subscription expired/cancelled)
            status_code = None
            if hasattr(exc, "response") and exc.response is not None:
                status_code = exc.response.status_code
            if status_code == 410:
                logger.info(f"Push subscription expired (410) — removing {sub.endpoint[:50]}...")
                endpoints_to_remove.append(sub.id)
            else:
                logger.error(f"Push notification failed for sub {sub.id}: {exc}")

    # Remove expired subscriptions
    for sub_id in endpoints_to_remove:
        await db.execute(delete(PushSubscription).where(PushSubscription.id == sub_id))

    if subs or endpoints_to_remove:
        try:
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to commit push notification updates: {e}")


async def save_subscription(
    user_id: str,
    endpoint: str,
    p256dh: str,
    auth: str,
    user_agent: Optional[str],
    db: AsyncSession,
) -> PushSubscription:
    """
    Create or update a push subscription.
    Upsert by endpoint — same endpoint updates keys and user_agent.
    """
    result = await db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    )
    sub = result.scalar_one_or_none()

    if sub:
        sub.p256dh = p256dh
        sub.auth = auth
        sub.user_agent = user_agent
        sub.last_used_at = datetime.now(timezone.utc)
        logger.info(f"Updated push subscription for user {user_id}")
    else:
        sub = PushSubscription(
            user_id=user_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_agent=user_agent,
        )
        db.add(sub)
        logger.info(f"Created new push subscription for user {user_id}")

    await db.commit()
    await db.refresh(sub)
    return sub


async def remove_subscription(endpoint: str, db: AsyncSession) -> None:
    """Delete a push subscription by endpoint URL."""
    await db.execute(delete(PushSubscription).where(PushSubscription.endpoint == endpoint))
    await db.commit()
    logger.info(f"Removed push subscription: {endpoint[:50]}...")
