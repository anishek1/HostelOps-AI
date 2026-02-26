"""
schemas/auth.py — HostelOps AI
================================
Pydantic schemas for authentication tokens.
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
