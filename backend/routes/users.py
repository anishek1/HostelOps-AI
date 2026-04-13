"""
routes/users.py — HostelOps AI
================================
User management routes: verify, deactivate, me.
Routes are thin — all logic delegated to services.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from schemas.enums import UserRole
from schemas.user import ChangePasswordRequest, StaffCreate, StaffRead, UserRead
from services.auth_service import get_current_user, require_role
from services.user_service import (
    change_own_password,
    create_staff_account,
    deactivate_user_account,
    list_users,
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


@router.get("", response_model=list[UserRead])
async def get_users(
    role: Optional[UserRole] = Query(None),
    is_verified: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Search by name or room number"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    warden: User = Depends(require_role(UserRole.warden)),
):
    """
    List users in the warden's hostel with optional filters.
    Requires warden role.
    """
    users = await list_users(
        db=db,
        hostel_id=warden.hostel_id,
        role=role,
        is_verified=is_verified,
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset,
    )
    return [UserRead.model_validate(u) for u in users]


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
    verifier: User = Depends(require_role(UserRole.warden)),
):
    """
    Activate a pending student account.
    Requires: assistant_warden, warden, or chief_warden role.
    """
    user = await verify_user_account(user_id=user_id, db=db, hostel_id=verifier.hostel_id)
    return UserRead.model_validate(user)


@router.delete("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    deactivator: User = Depends(require_role(UserRole.warden)),
):
    """
    Deactivate a student account (e.g., when student vacates).
    Requires: assistant_warden, warden, or chief_warden role.
    """
    user = await deactivate_user_account(user_id=user_id, db=db, hostel_id=deactivator.hostel_id)
    return UserRead.model_validate(user)


class RejectRequest(BaseModel):
    reason: str


@router.post("/{user_id}/reject", response_model=UserRead)
async def reject_pending_user(
    user_id: str,
    payload: RejectRequest,
    db: AsyncSession = Depends(get_db),
    warden: User = Depends(require_role(UserRole.warden)),
):
    """
    Reject a pending student registration.
    """
    user = await reject_user(user_id, payload.reason, warden.id, db, hostel_id=warden.hostel_id)
    return UserRead.model_validate(user)


class PasswordResetRequest(BaseModel):
    new_password: str


@router.patch("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    warden: User = Depends(require_role(UserRole.warden)),
):
    """
    Force reset a user's password.
    """
    await warden_reset_password(user_id, payload.new_password, warden.id, db, hostel_id=warden.hostel_id)
    return {"message": "Password reset successfully"}


@router.patch("/me/password", response_model=UserRead)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Self-service password change. Requires current password verification.
    Never uses passlib — uses verify_password from auth_service.
    """
    user = await change_own_password(
        user_id=current_user.id,
        current_password=payload.current_password,
        new_password=payload.new_password,
        db=db,
    )
    return UserRead.model_validate(user)


@router.post("/staff", response_model=StaffRead, status_code=201)
async def create_staff(
    payload: StaffCreate,
    db: AsyncSession = Depends(get_db),
    warden: User = Depends(require_role(UserRole.warden)),
):
    """
    Create a pre-verified staff account.
    """
    user = await create_staff_account(payload, warden.id, db, hostel_id=warden.hostel_id)
    return StaffRead.model_validate(user)


@router.get("/staff", response_model=list[StaffRead])
async def list_staff(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    warden: User = Depends(require_role(UserRole.warden)),
):
    """
    List all staff accounts.
    """
    from sqlalchemy import select
    query = (
        select(User)
        .where(User.role != UserRole.student)
        .where(User.is_active == True)  # noqa: E712
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    # Sprint 7: scope to warden's hostel
    if warden.hostel_id is not None:
        query = query.where(User.hostel_id == warden.hostel_id)
    result = await db.execute(query)
    staff_members = result.scalars().all()
    return [StaffRead.model_validate(s) for s in staff_members]

