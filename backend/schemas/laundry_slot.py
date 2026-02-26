"""
schemas/laundry_slot.py — HostelOps AI
========================================
Pydantic v2 schemas for the LaundrySlot entity.
"""

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict

from schemas.enums import SlotStatus


class LaundrySlotCreate(BaseModel):
    machine_id: str
    date: date
    start_time: time
    end_time: time


class LaundrySlotRead(BaseModel):
    id: str
    machine_id: str
    student_id: str
    date: date
    start_time: time
    end_time: time
    status: SlotStatus
    is_priority: bool
    priority_reason: str | None
    priority_approved_by: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LaundrySlotUpdate(BaseModel):
    status: SlotStatus | None = None

    model_config = ConfigDict(from_attributes=True)
