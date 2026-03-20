"""
routes/users.py — HostelOps AI
================================
User management routes: verify, deactivate, me.
Routes are thin — all logic delegated to services.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from schemas.enums import UserRole
from schemas.user import StaffCreate, StaffRead, UserRead
from services.auth_service import get_current_user, require_role
from services.user_service import (
    create_staff_account,
    deactivate_user_account,
    reject_user,
    verify_user_account,
    warden_reset_password,
)

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Return the current authenticated user's profile.
    Identity is extracted from the JWT bearer token.
    """
    return UserRead.model_validate(current_user)


@router.patch("/me/onboarding-seen", response_model=UserRead)
async def set_onboarding_seen(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark that the user has seen the frontend onboarding flow.
    """
    current_user.has_seen_onboarding = True
    await db.commit()
    await db.refresh(current_user)
    return UserRead.model_validate(current_user)


@router.post("/{user_id}/verify", response_model=UserRead)
async def verify_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    verifier: User = Depends(require_role(UserRole.assistant_warden, UserRole.warden)),
):
    """
    Activate a pending student account.
    Requires: assistant_warden or warden role.
    """
    user = await verify_user_account(user_id=user_id, db=db)
    return UserRead.model_validate(user)


@router.delete("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    deactivator: User = Depends(require_role(UserRole.assistant_warden, UserRole.warden)),
):
    """
    Deactivate a student account (e.g., when student vacates).
    Requires: assistant_warden or warden role.
    """
    user = await deactivate_user_account(user_id=user_id, db=db)
    return UserRead.model_validate(user)


class RejectRequest(BaseModel):
    reason: str


@router.post("/{user_id}/reject", response_model=UserRead)
async def reject_pending_user(
    user_id: str,
    payload: RejectRequest,
    db: AsyncSession = Depends(get_db),
    warden: User = Depends(require_role(UserRole.assistant_warden, UserRole.warden)),
):
    """
    Reject a pending student registration.
    """
    user = await reject_user(user_id, payload.reason, warden.id, db)
    return UserRead.model_validate(user)


class PasswordResetRequest(BaseModel):
    new_password: str


@router.patch("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    warden: User = Depends(require_role(UserRole.assistant_warden, UserRole.warden)),
):
    """
    Force reset a user's password.
    """
    await warden_reset_password(user_id, payload.new_password, warden.id, db)
    return {"message": "Password reset successfully"}


@router.post("/staff", response_model=StaffRead, status_code=201)
async def create_staff(
    payload: StaffCreate,
    db: AsyncSession = Depends(get_db),
    warden: User = Depends(require_role(UserRole.assistant_warden, UserRole.warden)),
):
    """
    Create a pre-verified staff account.
    """
    user = await create_staff_account(payload, warden.id, db)
    return StaffRead.model_validate(user)


@router.get("/staff", response_model=list[StaffRead])
async def list_staff(
    db: AsyncSession = Depends(get_db),
    warden: User = Depends(require_role(UserRole.assistant_warden, UserRole.warden)),
):
    """
    List all staff accounts.
    """
    from sqlalchemy import select
    # Return all users who aren't students
    result = await db.execute(
        select(User)
        .where(User.role != UserRole.student)
        .where(User.is_active == True)
        .order_by(User.created_at.desc())
    )
    staff_members = result.scalars().all()
    return [StaffRead.model_validate(s) for s in staff_members]

