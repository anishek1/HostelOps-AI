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

from services.auth_service import register_user, login_user
from middleware.rate_limiter import RateLimiter, get_rate_limiter

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
    return await register_user(payload, db)


@router.post("/login", response_model=Token)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
):
    """
    Authenticate and return a JWT token pair.
    - Returns 401 if user not found, password wrong, not verified, or deactivated.
    - Access token and refresh token both embed the 'role' claim.
    - Rate limited: 10 attempts per 15 minutes per room_number.
    """
    await rate_limiter.check_rate_limit(
        "login", payload.room_number, 10, 900,
        "Too many login attempts. Please try again later.",
    )
    return await login_user(payload, db)
