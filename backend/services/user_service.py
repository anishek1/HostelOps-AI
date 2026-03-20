"""
user_service.py — HostelOps AI
================================
Service functions for user management.
Called by routes/users.py — never contains FastAPI-specific code.
"""
import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.refresh_token import RefreshToken
from models.user import User
from schemas.enums import HostelMode, NotificationType, UserRole
from schemas.user import StaffCreate
from services.auth_service import hash_password
from services.notification_service import notify_user

logger = logging.getLogger(__name__)


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


# ---------------------------------------------------------------------------
# Sprint 6: Registration Rejection
# ---------------------------------------------------------------------------

async def reject_user(
    user_id: str,
    reason: str,
    warden_id: uuid.UUID,
    db: AsyncSession
) -> User:
    """
    Reject a pending student registration.
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already verified"
        )
    if getattr(user, "is_rejected", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already rejected"
        )

    user.is_rejected = True
    user.rejection_reason = reason
    user.is_verified = False

    await db.commit()
    await db.refresh(user)

    # Notify student
    await notify_user(
        recipient_id=user.id,
        title="Registration Rejected",
        body=f"Your registration was rejected. Reason: {reason}",
        notification_type=NotificationType.registration_rejected,
        db=db
    )

    logger.info(
        f"User {user.id} rejected by warden {warden_id}. Reason: {reason}"
    )
    return user


# ---------------------------------------------------------------------------
# Sprint 6: Warden Admin Operations
# ---------------------------------------------------------------------------

async def warden_reset_password(
    user_id: str,
    new_password: str,
    warden_id: uuid.UUID,
    db: AsyncSession
) -> User:
    """
    Force reset a user's password and log them out of all devices.
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 1. Update password
    user.hashed_password = hash_password(new_password)
    
    # 2. Revoke all refresh tokens (log out everywhere)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id)
        .values(revoked=True)
    )
    
    await db.commit()
    await db.refresh(user)

    # 3. Notify user
    await notify_user(
        recipient_id=user.id,
        title="Password Reset",
        body="Your password has been reset by the warden. Please wait for the new credentials.",
        notification_type=NotificationType.password_reset,
        db=db
    )

    logger.info(f"Password forcefully reset for user {user.id} by warden {warden_id}")
    return user


async def create_staff_account(
    staff_data: StaffCreate,
    warden_id: uuid.UUID,
    db: AsyncSession
) -> User:
    """
    Create a staff account (warden, assistant_warden, security, mess_staff).
    Staff accounts are pre-verified and do not need onboarding.
    """
    # Role validation
    allowed_roles = {
        UserRole.laundry_man, 
        UserRole.mess_secretary, 
        UserRole.mess_manager, 
        UserRole.assistant_warden
    }
    if staff_data.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create account with role '{staff_data.role.value}' via staff endpoint."
        )

    # Check if username/room_number exists
    result = await db.execute(select(User).where(User.room_number == staff_data.room_number))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this room number already exists."
        )

    staff_user = User(
        name=staff_data.name,
        room_number=staff_data.room_number,
        role=staff_data.role,
        hostel_mode=staff_data.hostel_mode,
        hashed_password=hash_password(staff_data.password),
        is_verified=True,
        is_active=True,
        has_seen_onboarding=True
    )

    db.add(staff_user)
    await db.commit()
    await db.refresh(staff_user)

    # Self-notification
    await notify_user(
        recipient_id=staff_user.id,
        title="Account Created",
        body=f"Your {staff_data.role.value} account has been created by the warden.",
        notification_type=NotificationType.registration_approved,
        db=db
    )

    logger.info(f"Staff account {staff_user.id} ({staff_data.role}) created by warden {warden_id}")
    return staff_user
