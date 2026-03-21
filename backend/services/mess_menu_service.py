"""
services/mess_menu_service.py — HostelOps AI
=============================================
Business logic for the Mess Menu feature (Sprint 7b).
Menus are scoped per hostel_id.
Golden Rule 31: Every query filters by hostel_id.
Golden Rule 16: await db.refresh(obj) after every commit.
"""
import logging
import uuid
from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.mess_menu import MessMenu
from schemas.mess import MessMenuCreate

logger = logging.getLogger(__name__)


async def create_menu(
    payload: MessMenuCreate,
    created_by: uuid.UUID,
    hostel_id: Optional[uuid.UUID],
    db: AsyncSession,
) -> MessMenu:
    """
    Create or replace a mess menu entry.
    Hostel-scoped. created_by is the warden/mess_manager who posted it.
    """
    menu = MessMenu(
        hostel_id=hostel_id,
        day_of_week=payload.day_of_week,
        meal=payload.meal,
        items=payload.items,
        valid_from=payload.valid_from,
        created_by=created_by,
    )
    db.add(menu)
    await db.commit()
    await db.refresh(menu)
    logger.info(f"Mess menu created for day={payload.day_of_week} meal={payload.meal.value} hostel={hostel_id}")
    return menu


async def get_current_menu(
    hostel_id: Optional[uuid.UUID],
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> list[MessMenu]:
    """
    Returns the current menu items for a hostel.
    Filters: hostel_id + valid_from <= today, ordered by valid_from desc.
    Returns the most recently published menu for each day/meal combination.
    """
    today = date.today()
    query = (
        select(MessMenu)
        .where(MessMenu.valid_from <= today)
        .order_by(MessMenu.valid_from.desc(), MessMenu.day_of_week, MessMenu.meal)
    )
    if hostel_id is not None:
        query = query.where(MessMenu.hostel_id == hostel_id)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
