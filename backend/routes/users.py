"""
routes/users.py — HostelOps AI
================================
User management routes: verify, deactivate, me.
Routes are thin — all logic delegated to services.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from schemas.enums import NotificationType, UserRole
from schemas.user import UserRead
from services.auth_service import get_current_user, require_role
from services.notification_service import notify_user

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Return the current authenticated user's profile.
    Identity is extracted from the JWT bearer token.
    """
    return UserRead(
        id=str(current_user.id),
        name=current_user.name,
        room_number=current_user.room_number,
        role=current_user.role,
        hostel_mode=current_user.hostel_mode,
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.post("/{user_id}/verify", response_model=UserRead)
async def verify_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    verifier: User = Depends(require_role(UserRole.assistant_warden, UserRole.warden)),
):
    """
    Activate a pending student account.
    Requires: assistant_warden or warden role.
    Notifies the student that their account is now active.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid user ID format.")

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
        notification_type=NotificationType.complaint_resolved,  # Using best-fit type; extend in future sprint
        db=db,
    )

    return UserRead(
        id=str(user.id),
        name=user.name,
        room_number=user.room_number,
        role=user.role,
        hostel_mode=user.hostel_mode,
        is_verified=user.is_verified,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.delete("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    deactivator: User = Depends(require_role(UserRole.assistant_warden, UserRole.warden)),
):
    """
    Deactivate a student account (e.g., when student vacates).
    Requires: assistant_warden or warden role.
    Deactivated users cannot log in.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid user ID format.")

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already deactivated.")

    user.is_active = False

    return UserRead(
        id=str(user.id),
        name=user.name,
        room_number=user.room_number,
        role=user.role,
        hostel_mode=user.hostel_mode,
        is_verified=user.is_verified,
        is_active=user.is_active,
        created_at=user.created_at,
    )
