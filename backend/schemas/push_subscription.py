"""
schemas/push_subscription.py — HostelOps AI
=============================================
Pydantic v2 schemas for push notification subscriptions.
Sprint 5: New file.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscribeRequest(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys
    user_agent: Optional[str] = None


class PushSubscriptionRead(BaseModel):
    id: str
    user_id: str
    endpoint: str
    created_at: datetime

    @field_validator("id", "user_id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    model_config = {"from_attributes": True}
