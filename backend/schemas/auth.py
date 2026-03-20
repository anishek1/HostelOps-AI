"""
schemas/auth.py — HostelOps AI
================================
Pydantic schemas for authentication tokens.
Sprint 6: Added LoginResponse with full user object.
"""

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: str | None = None
    role: str | None = None


class LoginRequest(BaseModel):
    room_number: str
    password: str


class LoginResponse(BaseModel):
    """Sprint 6: Login response includes full user object for frontend onboarding flow."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserRead"

    model_config = {"from_attributes": True}


# Defer import to avoid circular dependency
from schemas.user import UserRead  # noqa: E402
LoginResponse.model_rebuild()
