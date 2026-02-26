"""
schemas/user.py — HostelOps AI
===============================
Pydantic v2 schemas for the User entity.
These are the single source of truth — routes and services MUST use these.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

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


class UserRead(UserBase):
    id: str
    is_verified: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: str | None = None
    room_number: str | None = None

    model_config = ConfigDict(from_attributes=True)
