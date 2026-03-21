"""
schemas/hostel.py — HostelOps AI
===================================
Pydantic v2 schemas for the Hostel entity.
Sprint 7: Multi-tenant architecture.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from schemas.enums import HostelMode, UserRole


class HostelSetupRequest(BaseModel):
    """
    Request body for POST /api/hostels/setup.
    Creates a hostel + the first warden account in one call.
    """
    # Hostel details
    hostel_name: str
    hostel_mode: HostelMode
    total_floors: int = 3
    total_students_capacity: int = 200

    # Warden account details
    warden_name: str
    warden_room_number: str   # used as login identifier
    warden_password: str


class HostelRead(BaseModel):
    """Full hostel info — returned to the warden after setup."""
    id: str
    name: str
    code: str
    mode: HostelMode
    total_floors: int
    total_students_capacity: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        return str(v) if v is not None else None


class HostelPublicInfo(BaseModel):
    """Minimal hostel info returned by GET /api/hostels/{code}/info (public)."""
    name: str
    mode: HostelMode
    code: str


class HostelSetupResponse(BaseModel):
    """Response returned after successful hostel setup."""
    hostel: HostelRead
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
