"""
schemas/notice.py — HostelOps AI
===================================
Pydantic schemas for the Notice Board feature (Sprint 7b).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class NoticeCreate(BaseModel):
    title: str
    body: str
    priority: str = "normal"


class NoticeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    hostel_id: Optional[str] = None
    title: str
    body: str
    priority: str
    created_by: str
    created_at: datetime

    @field_validator("id", "hostel_id", "created_by", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        return str(v) if v is not None else None
