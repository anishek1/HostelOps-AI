"""
routes/auth.py — HostelOps AI
================================
Authentication routes: register and login.
Routes are thin — all logic delegated to services.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from schemas.auth import LoginRequest, Token
from schemas.enums import NotificationType, UserRole
from schemas.user import UserCreate, UserRead
from services.auth_service import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from services.notification_service import notify_all_by_role

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account.
    - College mode: requires roll_number and erp_document_url.
    - Autonomous mode: name + room_number only.
    - Account starts as is_verified=False — must be approved by Assistant Warden.
    - Notifies all Assistant Wardens of the new pending registration.
    """
    # Validate college-mode requirements
    if payload.hostel_mode.value == "college":
        if not payload.roll_number:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="roll_number is required for college hostel mode.",
            )
        if not payload.erp_document_url:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="erp_document_url is required for college hostel mode.",
            )

    # Check for duplicate room_number + role combination (optional guard)
    existing = await db.execute(
        select(User).where(
            User.room_number == payload.room_number,
            User.role == payload.role,
            User.is_active == True,  # noqa: E712
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active account with this room number and role already exists.",
        )

    user = User(
        name=payload.name,
        room_number=payload.room_number,
        role=payload.role,
        hostel_mode=payload.hostel_mode,
        hashed_password=hash_password(payload.password),
        roll_number=payload.roll_number,
        erp_document_url=payload.erp_document_url,
        is_verified=False,
        is_active=True,
    )
    db.add(user)
    await db.flush()  # Get the UUID assigned before notifications

    # Notify all assistant wardens
    await notify_all_by_role(
        role=UserRole.assistant_warden,
        title="New Registration Pending",
        body=f"Student '{payload.name}' (Room {payload.room_number}) has registered and requires verification.",
        notification_type=NotificationType.registration_pending,
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


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate and return a JWT token pair.
    - Returns 401 if user not found, password wrong, not verified, or deactivated.
    - Access token and refresh token both embed the 'role' claim.
    """
    result = await db.execute(
        select(User).where(User.room_number == payload.room_number)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect room number or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not yet verified. Please wait for Assistant Warden approval.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been deactivated. Please contact the warden.",
        )

    token_data = {"sub": str(user.id), "role": user.role.value}
    return Token(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        token_type="bearer",
    )
