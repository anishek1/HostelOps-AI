"""
schemas/notification.py — HostelOps AI
=========================================
Pydantic v2 schemas for the Notification entity.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas.enums import NotificationType


class NotificationCreate(BaseModel):
    recipient_id: str
    title: str
    body: str
    type: NotificationType


class NotificationRead(BaseModel):
    id: str
    recipient_id: str
    title: str
    body: str
    type: NotificationType
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
