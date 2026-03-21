"""
services/notice_service.py — HostelOps AI
==========================================
Business logic for the Notice Board feature (Sprint 7b).
All notices are scoped per hostel_id (Golden Rule 31).
Golden Rule 16: await db.refresh(obj) after every commit.
"""
import logging
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.notice import Notice
from schemas.notice import NoticeCreate

logger = logging.getLogger(__name__)


async def create_notice(
    payload: NoticeCreate,
    created_by: uuid.UUID,
    hostel_id: Optional[uuid.UUID],
    db: AsyncSession,
) -> Notice:
    """Create a notice. Only wardens may call this."""
    notice = Notice(
        hostel_id=hostel_id,
        title=payload.title,
        body=payload.body,
        priority=payload.priority,
        created_by=created_by,
    )
    db.add(notice)
    await db.commit()
    await db.refresh(notice)
    logger.info(f"Notice created by {created_by} in hostel {hostel_id}: '{payload.title}'")
    return notice


async def get_notices(
    hostel_id: Optional[uuid.UUID],
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> list[Notice]:
    """
    Returns paginated notices for a hostel, newest first.
    Golden Rule 31: scoped to hostel_id.
    """
    query = select(Notice).order_by(Notice.created_at.desc())
    if hostel_id is not None:
        query = query.where(Notice.hostel_id == hostel_id)
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


async def delete_notice(
    notice_id: str,
    hostel_id: Optional[uuid.UUID],
    db: AsyncSession,
) -> None:
    """
    Delete a notice. Verifies it belongs to the warden's hostel.
    Raises 404 if not found, 403 if hostel mismatch.
    """
    try:
        nid = uuid.UUID(notice_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid notice ID format.",
        )

    notice = await db.get(Notice, nid)
    if not notice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found.")
    if hostel_id is not None and notice.hostel_id != hostel_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this notice.")

    await db.delete(notice)
    await db.commit()
    logger.info(f"Notice {notice_id} deleted")
