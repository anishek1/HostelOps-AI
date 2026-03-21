"""
routes/notices.py — HostelOps AI
====================================
Notice board endpoints (Sprint 7b).
Wardens post notices; all hostel residents can read them.
Routes are thin — all logic in services/notice_service.py.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from schemas.enums import UserRole
from schemas.notice import NoticeCreate, NoticeRead
from services.auth_service import get_current_user, require_role
from services.notice_service import create_notice, delete_notice, get_notices

logger = logging.getLogger(__name__)

router = APIRouter()

WARDEN_ROLES = (UserRole.assistant_warden, UserRole.warden, UserRole.chief_warden)


@router.post("/", response_model=NoticeRead, status_code=status.HTTP_201_CREATED)
async def post_notice(
    payload: NoticeCreate,
    current_user: User = Depends(require_role(*WARDEN_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Create a notice (warden roles only)."""
    notice = await create_notice(
        payload=payload,
        created_by=current_user.id,
        hostel_id=current_user.hostel_id,
        db=db,
    )
    return NoticeRead.model_validate(notice)


@router.get("/", response_model=List[NoticeRead])
async def list_notices(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated notices for the current user's hostel."""
    notices = await get_notices(
        hostel_id=current_user.hostel_id,
        db=db,
        limit=limit,
        offset=offset,
    )
    return [NoticeRead.model_validate(n) for n in notices]


@router.delete("/{notice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_notice(
    notice_id: str,
    current_user: User = Depends(require_role(*WARDEN_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a notice (warden roles only)."""
    await delete_notice(
        notice_id=notice_id,
        hostel_id=current_user.hostel_id,
        db=db,
    )
