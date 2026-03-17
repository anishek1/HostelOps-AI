"""
schemas/refresh_token.py — HostelOps AI
=========================================
Pydantic v2 schemas for the RefreshToken entity.
Sprint 5: New file — DB-backed refresh token system.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class RefreshTokenRead(BaseModel):
    id: str
    user_id: str
    expires_at: datetime
    revoked: bool
    created_at: datetime
    ip_address: Optional[str] = None

    @field_validator("id", "user_id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    model_config = {"from_attributes": True}
