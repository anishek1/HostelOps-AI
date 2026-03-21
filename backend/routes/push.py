"""
routes/push.py — HostelOps AI
================================
Push notification subscription management endpoints.
Students and staff register their browser subscriptions here.
Sprint 5: New route file.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.user import User
from schemas.push_subscription import PushSubscribeRequest, PushSubscriptionRead
from services import push_service
from services.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """
    Return the VAPID public key needed by the browser for push subscription.
    Public endpoint — no auth required.
    """
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=503,
            detail="Push notifications are not configured on this server.",
        )
    return {"public_key": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe", response_model=PushSubscriptionRead)
async def subscribe(
    payload: PushSubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Save (or update) a browser push subscription.
    Each device/browser gets its own subscription.
    """
    sub = await push_service.save_subscription(
        user_id=str(current_user.id),
        endpoint=payload.endpoint,
        p256dh=payload.keys.p256dh,
        auth=payload.keys.auth,
        user_agent=payload.user_agent,
        db=db,
    )
    logger.info(f"User {current_user.id} subscribed to push notifications")
    return PushSubscriptionRead.model_validate(sub)


@router.delete("/unsubscribe")
async def unsubscribe(
    endpoint: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a push subscription by endpoint URL.
    Users can only unsubscribe their own subscriptions.
    """
    await push_service.remove_subscription(endpoint, str(current_user.id), db)
    logger.info(f"User {current_user.id} unsubscribed push endpoint")
    return {"status": "unsubscribed"}
