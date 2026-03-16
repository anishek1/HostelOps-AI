"""
schemas/laundry.py — HostelOps AI
====================================
Pydantic schemas for laundry slots and machines (Sprint 4).
Field validators convert UUID → str per Golden Rule 17.
"""
import logging
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from schemas.enums import LaundrySlotStatus, MachineStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Machine schemas
# ---------------------------------------------------------------------------

class MachineCreate(BaseModel):
    name: str
    floor: int


class MachineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    floor: Optional[int] = None
    status: MachineStatus
    is_active: bool
    last_reported_issue: Optional[str] = None
    created_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        return str(v) if v is not None else None


class MachineStatusUpdate(BaseModel):
    status: MachineStatus


# ---------------------------------------------------------------------------
# LaundrySlot schemas
# ---------------------------------------------------------------------------

class LaundrySlotCreate(BaseModel):
    machine_id: str
    slot_date: date
    slot_time: str  # e.g. "08:00-09:00"


class LaundrySlotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    machine_id: str
    student_id: Optional[str] = None
    slot_date: Optional[date] = None
    slot_time: Optional[str] = None
    booking_status: LaundrySlotStatus
    priority_score: Optional[float] = None
    booked_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    @field_validator("id", "machine_id", "student_id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        return str(v) if v is not None else None


class LaundryBookingResponse(BaseModel):
    slot_id: str
    machine_name: str
    slot_date: Optional[date]
    slot_time: Optional[str]
    booking_status: LaundrySlotStatus
    message: str


# ---------------------------------------------------------------------------
# Laundry Agent output schema
# ---------------------------------------------------------------------------

class LaundryRoutingResult(BaseModel):
    action_taken: str  # e.g. "reported_machine_issue", "booked_slot", "escalated"
    assigned_to: Optional[str] = None  # user_id of laundry_man or warden
    notes: Optional[str] = None
