"""
routes/hostel_config.py — HostelOps AI
========================================
Hostel configuration routes.
GET: any authenticated user (to read thresholds).
PATCH: assistant_warden or warden only.
Routes are thin — all logic delegated to hostel_config_service.
Sprint 5: New route file.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from schemas.enums import UserRole
from schemas.hostel_config import HostelConfigRead, HostelConfigUpdate
from services import hostel_config_service
from services.auth_service import get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=HostelConfigRead)
async def get_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the current hostel operational configuration.
    Any authenticated user may read this (students need it too for display).
    """
    config = await hostel_config_service.get_config(db)
    return HostelConfigRead.model_validate(config)


@router.patch("/", response_model=HostelConfigRead)
async def update_config(
    updates: HostelConfigUpdate,
    current_user: User = Depends(
        require_role(UserRole.assistant_warden, UserRole.warden, UserRole.chief_warden)
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Update hostel configuration. Warden-level roles only.
    Only provided (non-None) fields are updated.
    """
    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update provided.")

    config = await hostel_config_service.update_config(update_dict, db)
    logger.info(f"Config updated by {current_user.role.value} ({current_user.id}): {list(update_dict.keys())}")
    return HostelConfigRead.model_validate(config)
