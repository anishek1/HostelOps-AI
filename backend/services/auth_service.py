"""
services/auth_service.py — HostelOps AI
==========================================
All authentication and authorisation business logic.
Routes call these functions — zero logic in routes.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import bcrypt

from config import settings
from database import get_db
from models.user import User
from schemas.enums import UserRole

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    # bcrypt requires bytes
    salt = bcrypt.gensalt()
    # truncate to 72 bytes to avoid bcrypt error if someone inputs super long password
    pwd_bytes = password.encode('utf-8')[:72] 
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """Compare plain-text password against a stored bcrypt hash."""
    pwd_bytes = plain.encode('utf-8')[:72]
    hash_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


# ---------------------------------------------------------------------------
# JWT token creation
# ---------------------------------------------------------------------------

def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token.
    Embeds 'role' and 'sub' (user_id) as claims.
    Expires in ACCESS_TOKEN_EXPIRE_HOURS.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    payload.update({"exp": expire, "type": "access"})
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Create a signed JWT refresh token.
    Expires in REFRESH_TOKEN_EXPIRE_DAYS.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload.update({"exp": expire, "type": "refresh"})
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Raises HTTPException 401 on any failure.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

_bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: extracts and validates the JWT bearer token,
    then fetches the user from the database.
    Raises 401 if token is invalid or user not found.
    """
    token = credentials.credentials
    payload = decode_token(token)

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim.",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user


def require_role(*roles: UserRole):
    """
    FastAPI dependency factory.
    Returns a dependency that raises 403 if the current user's role
    is not in the allowed list.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(UserRole.warden))])
    Or as a parameter:
        async def route(current_user: User = Depends(require_role(UserRole.assistant_warden, UserRole.warden))):
    """
    async def _role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {[r.value for r in roles]}",
            )
        return current_user

    return _role_checker


# ---------------------------------------------------------------------------
# Business Logic
# ---------------------------------------------------------------------------

async def register_user(payload, db: AsyncSession):
    from schemas.user import UserRead
    from schemas.enums import NotificationType
    from services.notification_service import notify_all_by_role

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

async def login_user(payload, db: AsyncSession):
    from schemas.auth import Token
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

