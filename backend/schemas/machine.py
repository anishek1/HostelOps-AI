"""
schemas/machine.py — HostelOps AI
====================================
Pydantic v2 schemas for the Machine entity.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MachineCreate(BaseModel):
    name: str


class MachineRead(BaseModel):
    id: str
    name: str
    is_active: bool
    last_reported_issue: str | None
    repaired_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MachineUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    last_reported_issue: str | None = None
    repaired_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
