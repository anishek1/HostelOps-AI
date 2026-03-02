"""
routes/complaints.py — HostelOps AI
======================================
Complaint endpoints — thin routes that call services only.
All business logic lives in services/complaint_service.py.
LLM classification runs asynchronously via Celery — routes return immediately.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.complaint import ComplaintCreate, ComplaintRead
from schemas.enums import ComplaintStatus, UserRole
from services.auth_service import get_current_user, require_role
from services.complaint_service import (
    VALID_TRANSITIONS,
    create_complaint,
    get_complaint,
    transition_complaint,
)
from models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Response schema for complaint creation
# ---------------------------------------------------------------------------

class ComplaintCreatedResponse(BaseModel):
    complaint_id: str
    status: str
    message: str


class StatusUpdateRequest(BaseModel):
    status: ComplaintStatus


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
    data: ComplaintCreate,
    current_user: User = Depends(require_role(UserRole.student)),
    db: AsyncSession = Depends(get_db),
):
    complaint = await create_complaint(
        student_id=str(current_user.id),
        data=data,
        db=db,
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
# GET /api/complaints/{complaint_id} — view a complaint
# ---------------------------------------------------------------------------

@router.get(
    "/{complaint_id}",
    response_model=ComplaintRead,
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

    # Build the ComplaintRead response manually (handles UUID → str conversion)
    return ComplaintRead(
        id=str(complaint.id),
        student_id=str(complaint.student_id),
        text=complaint.text if not complaint.is_anonymous else "[Anonymous]",
        is_anonymous=complaint.is_anonymous,
        category=complaint.category,
        severity=complaint.severity,
        status=complaint.status,
        assigned_to=str(complaint.assigned_to) if complaint.assigned_to else None,
        confidence_score=complaint.confidence_score,
        ai_suggested_category=complaint.ai_suggested_category,
        ai_suggested_assignee=str(complaint.ai_suggested_assignee) if complaint.ai_suggested_assignee else None,
        requires_approval=complaint.requires_approval,
        classified_by=complaint.classified_by,
        override_reason=complaint.override_reason,
        flagged_input=complaint.flagged_input,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
    )


# ---------------------------------------------------------------------------
# PATCH /api/complaints/{complaint_id}/status — update status (staff only)
# ---------------------------------------------------------------------------

STAFF_ROLES = (
    UserRole.laundry_man,
    UserRole.mess_secretary,
    UserRole.mess_manager,
    UserRole.assistant_warden,
    UserRole.warden,
    UserRole.chief_warden,
)


@router.patch(
    "/{complaint_id}/status",
    response_model=ComplaintRead,
    summary="Update complaint status (staff only)",
)
async def update_complaint_status(
    complaint_id: str,
    body: StatusUpdateRequest,
    current_user: User = Depends(require_role(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    complaint = await get_complaint(
        complaint_id=complaint_id,
        requesting_user_id=str(current_user.id),
        requesting_user_role=current_user.role,
        db=db,
    )

    try:
        updated = await transition_complaint(
            complaint_id=complaint_id,
            from_state=complaint.status,
            to_state=body.status,
            triggered_by=str(current_user.id),
            db=db,
            note=f"Manual update by {current_user.role.value}",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ComplaintRead(
        id=str(updated.id),
        student_id=str(updated.student_id),
        text=updated.text,
        is_anonymous=updated.is_anonymous,
        category=updated.category,
        severity=updated.severity,
        status=updated.status,
        assigned_to=str(updated.assigned_to) if updated.assigned_to else None,
        confidence_score=updated.confidence_score,
        ai_suggested_category=updated.ai_suggested_category,
        ai_suggested_assignee=str(updated.ai_suggested_assignee) if updated.ai_suggested_assignee else None,
        requires_approval=updated.requires_approval,
        classified_by=updated.classified_by,
        override_reason=updated.override_reason,
        flagged_input=updated.flagged_input,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


# ---------------------------------------------------------------------------
# POST /api/complaints/{complaint_id}/reopen — student reopens resolved complaint
# ---------------------------------------------------------------------------

class ReopenResponse(BaseModel):
    complaint_id: str
    status: str
    message: str


@router.post(
    "/{complaint_id}/reopen",
    response_model=ReopenResponse,
    summary="Reopen a resolved complaint (student only)",
)
async def reopen_complaint(
    complaint_id: str,
    current_user: User = Depends(require_role(UserRole.student)),
    db: AsyncSession = Depends(get_db),
):
    complaint = await get_complaint(
        complaint_id=complaint_id,
        requesting_user_id=str(current_user.id),
        requesting_user_role=current_user.role,
        db=db,
    )

    # Students can only reopen their own complaints
    if str(complaint.student_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reopen your own complaints.",
        )

    if complaint.status != ComplaintStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reopen complaint with status '{complaint.status.value}'. "
                   "Complaint must be in RESOLVED state.",
        )

    try:
        updated = await transition_complaint(
            complaint_id=complaint_id,
            from_state=ComplaintStatus.RESOLVED,
            to_state=ComplaintStatus.REOPENED,
            triggered_by=str(current_user.id),
            db=db,
            note="Reopened by student",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Notify wardens about the reopened complaint
    try:
        from services.notification_service import notify_all_by_role
        from schemas.enums import NotificationType
        await notify_all_by_role(
            role=UserRole.assistant_warden,
            title="Complaint Reopened",
            body=f"A resolved complaint has been reopened by a student. ID: {complaint_id[:8].upper()}.",
            notification_type=NotificationType.approval_needed,
            db=db,
        )
    except Exception:
        pass  # Notification failure is non-critical

    return ReopenResponse(
        complaint_id=str(updated.id),
        status=updated.status.value,
        message="Your complaint has been reopened. A warden will review it shortly.",
    )
