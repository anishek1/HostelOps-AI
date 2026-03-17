"""
schemas/hostel_config.py — HostelOps AI
=========================================
Pydantic v2 schemas for the HostelConfig entity.
Single source of truth for config request/response shapes.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class HostelConfigBase(BaseModel):
    hostel_name: str
    hostel_mode: str
    total_floors: int
    total_students_capacity: int
    complaint_rate_limit: int
    approval_queue_timeout_minutes: int
    complaint_confidence_threshold: float
    mess_alert_threshold: float
    mess_critical_threshold: float
    mess_min_participation: float
    mess_min_responses: int
    laundry_slots_start_hour: int
    laundry_slots_end_hour: int
    laundry_slot_duration_hours: int
    laundry_noshow_penalty_hours: int
    laundry_cancellation_deadline_minutes: int


class HostelConfigRead(HostelConfigBase):
    id: str
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    model_config = {"from_attributes": True}


class HostelConfigUpdate(BaseModel):
    hostel_name: Optional[str] = None
    hostel_mode: Optional[str] = None
    total_floors: Optional[int] = None
    total_students_capacity: Optional[int] = None
    complaint_rate_limit: Optional[int] = None
    approval_queue_timeout_minutes: Optional[int] = None
    complaint_confidence_threshold: Optional[float] = None
    mess_alert_threshold: Optional[float] = None
    mess_critical_threshold: Optional[float] = None
    mess_min_participation: Optional[float] = None
    mess_min_responses: Optional[int] = None
    laundry_slots_start_hour: Optional[int] = None
    laundry_slots_end_hour: Optional[int] = None
    laundry_slot_duration_hours: Optional[int] = None
    laundry_noshow_penalty_hours: Optional[int] = None
    laundry_cancellation_deadline_minutes: Optional[int] = None
