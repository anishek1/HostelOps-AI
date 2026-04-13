"""
routes/auth.py — HostelOps AI
================================
Authentication routes: register, login, refresh, logout.
Routes are thin — all logic delegated to services.
Sprint 5: Added /refresh (token rotation) and /logout (revoke all tokens).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.rate_limiter import RateLimiter, get_rate_limiter
from schemas.auth import LoginRequest, LoginResponse, Token
from schemas.user import UserCreate, UserRead
from services.auth_service import (
    create_access_token,
    create_refresh_token_db,
    get_current_user,
    login_user,
    register_user,
    revoke_all_user_tokens,
    revoke_refresh_token,
    verify_refresh_token_db,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
):
    """
    Authenticate and return a JWT access token + DB-backed refresh token.
    - Returns 401 if user not found, password wrong, not verified, or deactivated.
    - Access token and refresh token both embed the 'role' claim.
    - Rate limited: 10 attempts per 15 minutes per room_number.
    - Sprint 5: refresh token is now DB-backed (opaque, rotated on each use).
    """
    await rate_limiter.check_rate_limit(
        "login", payload.room_number, 10, 900,
        "Too many login attempts. Please try again later.",
    )
    ip_address = request.client.host if request.client else None
    return await login_user(payload, db, ip_address=ip_address)


# ---------------------------------------------------------------------------
# Refresh (Sprint 5)
# ---------------------------------------------------------------------------

class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=Token)
async def refresh_token(
    payload: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a valid DB-backed refresh token for a new token pair.
    Implements token rotation: old token is revoked, new one issued.
    Theft detection: if a revoked token is presented, ALL user tokens are revoked.
    """
    user, token_obj = await verify_refresh_token_db(payload.refresh_token, db)

    if not user or not token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    # Rotate: revoke old token
    await revoke_refresh_token(token_obj, db)

    # Issue new token pair
    ip_address = request.client.host if request.client else None
    token_data = {"sub": str(user.id), "role": user.role.value}
    new_access = create_access_token(token_data)
    new_refresh = await create_refresh_token_db(str(user.id), ip_address, db)

    logger.info(f"Token rotated for user {user.id}")
    return Token(access_token=new_access, refresh_token=new_refresh, token_type="bearer")


# ---------------------------------------------------------------------------
# Logout (Sprint 5)
# ---------------------------------------------------------------------------

@router.post("/logout")
async def logout(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke all refresh tokens for the current user.
    The access token remains valid until expiry (stateless) but no refresh is possible.
    """
    count = await revoke_all_user_tokens(str(current_user.id), db)
    logger.info(f"User {current_user.id} logged out — {count} refresh token(s) revoked")
    return {"message": "Logged out successfully.", "tokens_revoked": count}
