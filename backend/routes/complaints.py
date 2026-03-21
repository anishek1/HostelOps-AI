"""
routes/complaints.py — HostelOps AI
======================================
Complaint endpoints — thin routes that call services only.
All business logic lives in services/complaint_service.py.
LLM classification runs asynchronously via Celery — routes return immediately.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.audit_log import AuditLog
from models.user import User
from schemas.complaint import ComplaintCreate, ComplaintRead, ComplaintReadAnonymous, ComplaintTemplateRead
from schemas.enums import ComplaintCategory, ComplaintSeverity, ComplaintStatus, UserRole
from services.auth_service import get_current_user, require_role
from services.complaint_service import (
    VALID_TRANSITIONS,
    create_complaint,
    get_complaint,
    get_my_complaints,
    list_complaints,
    staff_update_progress,
    student_confirm_resolution,
    student_reopen_complaint,
    transition_complaint,
)
from services import approval_queue_service as aqs
from middleware.rate_limiter import RateLimiter, get_rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Response/Request schemas
# ---------------------------------------------------------------------------


class ComplaintCreatedResponse(BaseModel):
    complaint_id: str
    status: str
    message: str


class StatusUpdateRequest(BaseModel):
    status: ComplaintStatus


class ReopenRequest(BaseModel):
    reason: str


class ReopenResponse(BaseModel):
    complaint_id: str
    status: str
    message: str


class EscalateRequest(BaseModel):
    reason: str


class ConfirmResponse(BaseModel):
    complaint_id: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# Helper: Complaint ORM → ComplaintRead
# ---------------------------------------------------------------------------


def serialize_complaint(complaint, requesting_user) -> ComplaintRead | ComplaintReadAnonymous:
    """
    Returns the correct schema based on anonymity and role.
    - If not anonymous: always return ComplaintRead (student_id visible)
    - If anonymous AND requesting user is student: return ComplaintRead (they filed it, they know)
    - If anonymous AND requesting user is staff (not warden/chief_warden): return ComplaintReadAnonymous (hide student_id)
    - If anonymous AND requesting user is warden or chief_warden: return ComplaintRead (wardens can see all)
    """
    WARDEN_ROLES = [UserRole.warden, UserRole.chief_warden, UserRole.assistant_warden]
    
    if not complaint.is_anonymous:
        return ComplaintRead.model_validate(complaint)
    
    # Anonymous complaint
    if requesting_user.role in WARDEN_ROLES:
        return ComplaintRead.model_validate(complaint)  # wardens see everything
    
    if str(requesting_user.id) == str(complaint.student_id):
        return ComplaintRead.model_validate(complaint)  # student sees their own
    
    # Staff or other roles — hide student_id
    return ComplaintReadAnonymous.model_validate(complaint)


# Staff roles used in role checks
STAFF_ROLES = (
    UserRole.laundry_man,
    UserRole.mess_secretary,
    UserRole.mess_manager,
    UserRole.assistant_warden,
    UserRole.warden,
    UserRole.chief_warden,
)

WARDEN_ROLES = (
    UserRole.assistant_warden,
    UserRole.warden,
    UserRole.chief_warden,
)


# ---------------------------------------------------------------------------
# POST /api/complaints/ — file a new complaint
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=ComplaintCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="File a new complaint",
    description=(
        "Creates a complaint in INTAKE state and immediately fires the background "
        "classification task. Response is always under 2 seconds — LLM runs async."
    ),
)
async def file_complaint(
    request: Request,
    data: ComplaintCreate,
    current_user: User = Depends(require_role(UserRole.student)),
    db: AsyncSession = Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
):
    # Rate limit: students can file max 5 complaints per day
    # Wardens skip rate limiting (handled by role check above — only students file complaints)
    await rate_limiter.check_rate_limit(
        "complaint", str(current_user.id), 5, 86400,
        "Rate limit exceeded. You can file up to 5 complaints per day.",
    )

    client_ip = request.client.host if request.client else "0.0.0.0"
    complaint = await create_complaint(
        student_id=str(current_user.id),
        data=data,
        db=db,
        ip_address=client_ip,
    )
    await db.flush()  # Ensure complaint.id is available before Celery task

    # Fire Celery task — non-blocking, response returns immediately
    from tasks.complaint_tasks import classify_and_route_complaint
    classify_and_route_complaint.delay(str(complaint.id))

    return ComplaintCreatedResponse(
        complaint_id=str(complaint.id),
        status=complaint.status.value,
        message=(
            "Your complaint has been received and is being reviewed. "
            "You will be notified once it is assigned."
        ),
    )


# ---------------------------------------------------------------------------
# GET /api/complaints/ — warden list with filters
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=List[ComplaintRead],
    summary="List all complaints in hostel (warden only)",
)
async def list_complaints_route(
    complaint_status: Optional[ComplaintStatus] = Query(None, alias="status"),
    category: Optional[ComplaintCategory] = Query(None),
    severity: Optional[ComplaintSeverity] = Query(None),
    search: Optional[str] = Query(None, description="Text search in complaint body"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(*WARDEN_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    complaints = await list_complaints(
        db=db,
        hostel_id=current_user.hostel_id,
        complaint_status=complaint_status,
        category=category,
        severity=severity,
        search=search,
        limit=limit,
        offset=offset,
    )
    return [serialize_complaint(c, current_user) for c in complaints]


# ---------------------------------------------------------------------------
# GET /api/complaints/templates — hardcoded quick-fill templates
# ---------------------------------------------------------------------------


@router.get(
    "/templates",
    response_model=List[ComplaintTemplateRead],
    summary="Get complaint quick-fill templates",
)
async def get_complaint_templates(
    current_user: User = Depends(get_current_user),
):
    from services.complaint_template_service import get_templates
    return get_templates()


# ---------------------------------------------------------------------------
# GET /api/complaints/my — student's own complaints
# ---------------------------------------------------------------------------


@router.get(
    "/my",
    response_model=List[ComplaintRead],
    summary="Get my complaints (student only)",
)
async def get_my_complaints_route(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(UserRole.student)),
    db: AsyncSession = Depends(get_db),
):
    complaints = await get_my_complaints(str(current_user.id), db, limit=limit, offset=offset)
    return [serialize_complaint(c, current_user) for c in complaints]


# ---------------------------------------------------------------------------
# GET /api/complaints/{complaint_id} — view a complaint
# ---------------------------------------------------------------------------


@router.get(
    "/{complaint_id}",
    response_model=ComplaintRead | ComplaintReadAnonymous,
    summary="Get complaint details",
)
async def get_complaint_details(
    complaint_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    complaint = await get_complaint(
        complaint_id=complaint_id,
        requesting_user_id=str(current_user.id),
        requesting_user_role=current_user.role,
        db=db,
    )
    return serialize_complaint(complaint, current_user)


# ---------------------------------------------------------------------------
# GET /api/complaints/{complaint_id}/timeline — audit log timeline
# ---------------------------------------------------------------------------


@router.get(
    "/{complaint_id}/timeline",
    summary="Get complaint status timeline",
)
async def get_complaint_timeline(
    complaint_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # First verify access
    complaint = await get_complaint(
        complaint_id=complaint_id,
        requesting_user_id=str(current_user.id),
        requesting_user_role=current_user.role,
        db=db,
    )

    # Fetch audit logs for this complaint
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.entity_type == "complaint")
        .where(AuditLog.entity_id == complaint_id)
        .order_by(AuditLog.created_at.asc())
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "action": log.action,
            "timestamp": log.created_at.isoformat(),
            "user_id": str(log.user_id),
        }
        for log in logs
    ]


# ---------------------------------------------------------------------------
# PATCH /api/complaints/{complaint_id}/status — update status (staff only)
# ---------------------------------------------------------------------------


@router.patch(
    "/{complaint_id}/status",
    response_model=ComplaintRead | ComplaintReadAnonymous,
    summary="Update complaint status (staff only)",
)
async def update_complaint_status(
    complaint_id: str,
    request: Request,
    body: StatusUpdateRequest,
    current_user: User = Depends(require_role(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "0.0.0.0"
    try:
        updated = await staff_update_progress(
            complaint_id=complaint_id,
            new_status=body.status,
            staff_id=str(current_user.id),
            db=db,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return serialize_complaint(updated, current_user)


# ---------------------------------------------------------------------------
# POST /api/complaints/{complaint_id}/confirm — student confirms resolution
# ---------------------------------------------------------------------------


@router.post(
    "/{complaint_id}/confirm",
    response_model=ConfirmResponse,
    summary="Confirm complaint resolution (student only)",
)
async def confirm_resolution(
    complaint_id: str,
    request: Request,
    current_user: User = Depends(require_role(UserRole.student)),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "0.0.0.0"
    try:
        complaint = await student_confirm_resolution(
            complaint_id=complaint_id,
            student_id=str(current_user.id),
            db=db,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ConfirmResponse(
        complaint_id=str(complaint.id),
        status=complaint.status.value,
        message="Thank you for confirming. Your complaint has been closed.",
    )


# ---------------------------------------------------------------------------
# POST /api/complaints/{complaint_id}/reopen — student reopens a complaint
# ---------------------------------------------------------------------------


@router.post(
    "/{complaint_id}/reopen",
    response_model=ReopenResponse,
    summary="Reopen a resolved complaint (student only)",
)
async def reopen_complaint(
    complaint_id: str,
    request: Request,
    body: ReopenRequest,
    current_user: User = Depends(require_role(UserRole.student)),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "0.0.0.0"
    try:
        updated = await student_reopen_complaint(
            complaint_id=complaint_id,
            student_id=str(current_user.id),
            reopen_reason=body.reason,
            db=db,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ReopenResponse(
        complaint_id=str(updated.id),
        status=updated.status.value,
        message="Your complaint has been reopened. A warden will review it shortly.",
    )


# ---------------------------------------------------------------------------
# POST /api/complaints/{complaint_id}/escalate — warden escalates
# ---------------------------------------------------------------------------


@router.post(
    "/{complaint_id}/escalate",
    response_model=ComplaintRead | ComplaintReadAnonymous,
    summary="Escalate a complaint (warden only)",
)
async def escalate_complaint(
    complaint_id: str,
    request: Request,
    body: EscalateRequest,
    current_user: User = Depends(require_role(*WARDEN_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "0.0.0.0"
    try:
        complaint = await aqs.escalate_complaint(
            complaint_id=complaint_id,
            warden_id=str(current_user.id),
            reason=body.reason,
            db=db,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return serialize_complaint(complaint, current_user)
