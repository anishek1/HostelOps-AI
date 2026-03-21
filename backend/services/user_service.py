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

from typing import Optional

logger = logging.getLogger(__name__)


async def verify_user_account(
    user_id: str,
    db: AsyncSession,
    hostel_id=None,
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

    query = select(User).where(User.id == uid)
    if hostel_id is not None:
        query = query.where(User.hostel_id == hostel_id)
    result = await db.execute(query)
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
    hostel_id=None,
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

    query = select(User).where(User.id == uid)
    if hostel_id is not None:
        query = query.where(User.hostel_id == hostel_id)
    result = await db.execute(query)
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
    db: AsyncSession,
    hostel_id=None,
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

    query = select(User).where(User.id == uid)
    if hostel_id is not None:
        query = query.where(User.hostel_id == hostel_id)
    result = await db.execute(query)
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
    db: AsyncSession,
    hostel_id=None,
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

    query = select(User).where(User.id == uid)
    if hostel_id is not None:
        query = query.where(User.hostel_id == hostel_id)
    result = await db.execute(query)
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
    db: AsyncSession,
    hostel_id=None,
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

    # Check if username/room_number exists (scoped to hostel)
    room_q = select(User).where(User.room_number == staff_data.room_number)
    if hostel_id is not None:
        room_q = room_q.where(User.hostel_id == hostel_id)
    result = await db.execute(room_q)
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
        has_seen_onboarding=True,
        hostel_id=hostel_id,  # Sprint 7: inherit from creating warden
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


# ---------------------------------------------------------------------------
# Sprint 7b: Warden list users
# ---------------------------------------------------------------------------

async def list_users(
    db: AsyncSession,
    hostel_id=None,
    role: Optional[UserRole] = None,
    is_verified: Optional[bool] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> list[User]:
    """
    List users in a hostel with optional filters.
    Golden Rule 31: always scoped by hostel_id when provided.
    """
    query = select(User).order_by(User.created_at.desc())

    if hostel_id is not None:
        query = query.where(User.hostel_id == hostel_id)
    if role is not None:
        query = query.where(User.role == role)
    if is_verified is not None:
        query = query.where(User.is_verified == is_verified)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        from sqlalchemy import or_
        query = query.where(
            or_(User.name.ilike(f"%{search}%"), User.room_number.ilike(f"%{search}%"))
        )

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Sprint 7b: Self-service password change
# ---------------------------------------------------------------------------

async def change_own_password(
    user_id: uuid.UUID,
    current_password: str,
    new_password: str,
    db: AsyncSession,
) -> User:
    """
    Student/staff changes their own password.
    Verifies the current password before updating.
    Raises 400 if current password is wrong.
    """
    from services.auth_service import verify_password

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    user.hashed_password = hash_password(new_password)
    await db.commit()
    await db.refresh(user)
    logger.info(f"User {user_id} changed their own password")
    return user
