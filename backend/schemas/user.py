"""
schemas/user.py — HostelOps AI
===============================
Pydantic v2 schemas for the User entity.
These are the single source of truth — routes and services MUST use these.
Sprint 6: Added is_rejected, rejection_reason, has_seen_onboarding to UserRead.
          Added StaffCreate and StaffRead schemas.
Sprint 7b: Added feedback_streak, ChangePasswordRequest, UserListParams.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from schemas.enums import HostelMode, UserRole


class UserBase(BaseModel):
    name: str
    room_number: str
    role: UserRole
    hostel_mode: HostelMode


class UserCreate(UserBase):
    password: str
    roll_number: str | None = None
    erp_document_url: str | None = None  # college mode only
    hostel_code: str  # Sprint 7: required — links student to their hostel


class UserRead(UserBase):
    id: str
    is_verified: bool
    is_active: bool
    is_rejected: bool = False
    rejection_reason: str | None = None
    has_seen_onboarding: bool = False
    feedback_streak: int = 0  # Sprint 7b
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        """Coerce UUID objects → str (Golden Rule 16)."""
        return str(v) if v is not None else None


class UserUpdate(BaseModel):
    name: str | None = None
    room_number: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Sprint 6: Staff management schemas
# ---------------------------------------------------------------------------

class StaffCreate(BaseModel):
    """Request body for warden creating a staff account."""
    name: str
    role: UserRole
    room_number: str
    password: str
    hostel_mode: HostelMode = HostelMode.college


class StaffRead(UserRead):
    """Response model for staff accounts — same fields as UserRead."""
    pass


# ---------------------------------------------------------------------------
# Sprint 7b: Self-service password change
# ---------------------------------------------------------------------------

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
