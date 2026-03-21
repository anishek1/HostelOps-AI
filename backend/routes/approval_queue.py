"""
routes/approval_queue.py — HostelOps AI
==========================================
Approval queue endpoints — warden review of AI classification suggestions.
Routes are thin — all logic in services/approval_queue_service.py.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from models.user import User
from schemas.approval_queue import ApprovalQueueItemRead
from schemas.complaint import ComplaintRead
from schemas.enums import (
    ComplaintCategory,
    ComplaintSeverity,
    OverrideReason,
    UserRole,
)
from services.auth_service import require_role
from services import approval_queue_service as aqs

logger = logging.getLogger(__name__)

router = APIRouter()

# Roles allowed to access the approval queue
WARDEN_ROLES = (UserRole.assistant_warden, UserRole.warden, UserRole.chief_warden)


# ---------------------------------------------------------------------------
# Request schemas (inline — thin route-level models)
# ---------------------------------------------------------------------------


class OverrideRequest(BaseModel):
    corrected_category: ComplaintCategory
    corrected_severity: ComplaintSeverity
    corrected_assignee_id: str
    reason: OverrideReason


class EscalateRequest(BaseModel):
    reason: str


# ---------------------------------------------------------------------------
# GET /api/approval-queue/ — list pending items
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=List[ApprovalQueueItemRead],
    summary="Get all pending approval queue items",
)
async def get_pending_approvals(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(*WARDEN_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    items = await aqs.get_pending_approvals(db, limit=limit, offset=offset)
    return [
        ApprovalQueueItemRead(
            id=str(item.id),
            complaint_id=str(item.complaint_id),
            ai_suggested_category=item.ai_suggested_category,
            ai_suggested_severity=item.ai_suggested_severity,
            ai_suggested_assignee=str(item.ai_suggested_assignee),
            confidence_score=item.confidence_score,
            status=item.status,
            reviewed_by=str(item.reviewed_by) if item.reviewed_by else None,
            override_reason=item.override_reason,
            created_at=item.created_at,
            reviewed_at=item.reviewed_at,
        )
        for item in items
    ]


# ---------------------------------------------------------------------------
# POST /api/approval-queue/{queue_item_id}/approve
# ---------------------------------------------------------------------------


@router.post(
    "/{queue_item_id}/approve",
    response_model=ComplaintRead,
    summary="Approve AI classification suggestion",
)
async def approve_suggestion(
    queue_item_id: str,
    request: Request,
    current_user: User = Depends(require_role(*WARDEN_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "0.0.0.0"
    try:
        complaint = await aqs.approve_ai_suggestion(
            queue_item_id, str(current_user.id), db, ip_address=client_ip
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _complaint_to_read(complaint)


# ---------------------------------------------------------------------------
# POST /api/approval-queue/{queue_item_id}/override
# ---------------------------------------------------------------------------


@router.post(
    "/{queue_item_id}/override",
    response_model=ComplaintRead,
    summary="Override AI classification with corrections",
)
async def override_suggestion(
    queue_item_id: str,
    request: Request,
    body: OverrideRequest,
    current_user: User = Depends(require_role(*WARDEN_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "0.0.0.0"
    try:
        complaint = await aqs.override_ai_suggestion(
            queue_item_id=queue_item_id,
            warden_id=str(current_user.id),
            corrected_category=body.corrected_category,
            corrected_severity=body.corrected_severity,
            corrected_assignee_id=body.corrected_assignee_id,
            reason=body.reason,
            db=db,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _complaint_to_read(complaint)


# ---------------------------------------------------------------------------
# Helper: Complaint ORM → ComplaintRead
# ---------------------------------------------------------------------------


def _complaint_to_read(c) -> ComplaintRead:
    """Convert a Complaint ORM instance to ComplaintRead schema."""
    return ComplaintRead.model_validate(c)
