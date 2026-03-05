"""
user_service.py — HostelOps AI
================================
Service functions for user management.
Called by routes/users.py — never contains FastAPI-specific code.
"""
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from schemas.enums import NotificationType, UserRole
from services.notification_service import notify_user


async def verify_user_account(
    user_id: str,
    db: AsyncSession,
) -> User:
    """
    Sets is_verified=True for a user.
    Called by Assistant Warden after reviewing registration.
    Raises 404 if user not found, 409 if already verified.
    Notifies the student that their account is active.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid user ID format.",
        )

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already verified.")

    user.is_verified = True

    # Notify the student
    await notify_user(
        recipient_id=user.id,
        title="Account Verified",
        body="Your account has been verified. You can now log in to HostelOps AI.",
        notification_type=NotificationType.complaint_resolved,
        db=db,
    )

    return user


async def deactivate_user_account(
    user_id: str,
    db: AsyncSession,
) -> User:
    """
    Sets is_active=False for a user.
    Called by Assistant Warden when student vacates.
    Raises 404 if user not found, 409 if already deactivated.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid user ID format.",
        )

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already deactivated.")

    user.is_active = False

    return user
