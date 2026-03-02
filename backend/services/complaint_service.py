"""
complaint_service.py — HostelOps AI
======================================
State machine and business logic for complaints.
This is the most critical service in the project.
The ONLY function that may change complaint.status is transition_complaint().
All state changes are recorded in audit_log automatically.
"""
import logging
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.audit_log import AuditLog
from models.approval_queue import ApprovalQueueItem
from models.complaint import Complaint
from schemas.enums import (
    ClassifiedBy,
    ComplaintCategory,
    ComplaintSeverity,
    ComplaintStatus,
    NotificationType,
    UserRole,
)
from middleware.prompt_sanitizer import sanitize_input

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State machine — valid transitions (from PRD.md Section 9.2)
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[ComplaintStatus, list[ComplaintStatus]] = {
    ComplaintStatus.INTAKE: [ComplaintStatus.CLASSIFIED, ComplaintStatus.ESCALATED],
    ComplaintStatus.CLASSIFIED: [ComplaintStatus.ASSIGNED, ComplaintStatus.AWAITING_APPROVAL],
    ComplaintStatus.AWAITING_APPROVAL: [ComplaintStatus.ASSIGNED, ComplaintStatus.ESCALATED],
    ComplaintStatus.ASSIGNED: [ComplaintStatus.IN_PROGRESS, ComplaintStatus.ESCALATED],
    ComplaintStatus.IN_PROGRESS: [ComplaintStatus.RESOLVED],
    ComplaintStatus.RESOLVED: [ComplaintStatus.REOPENED],
    ComplaintStatus.REOPENED: [ComplaintStatus.ASSIGNED],
    ComplaintStatus.ESCALATED: [ComplaintStatus.ASSIGNED],
}


# ---------------------------------------------------------------------------
# Core: transition_complaint — the ONLY function that changes status
# ---------------------------------------------------------------------------

async def transition_complaint(
    complaint_id: str,
    from_state: ComplaintStatus,
    to_state: ComplaintStatus,
    triggered_by: str,  # user_id or "system"
    db: AsyncSession,
    note: Optional[str] = None,
) -> Complaint:
    """
    The ONLY function allowed to change complaint.status.
    Validates the transition is legal before applying it.
    Writes to audit log automatically.
    Raises ValueError for invalid transitions.
    """
    allowed = VALID_TRANSITIONS.get(from_state, [])
    if to_state not in allowed:
        raise ValueError(
            f"Invalid transition: {from_state.value} → {to_state.value}. "
            f"Allowed from {from_state.value}: {[s.value for s in allowed]}"
        )

    # Fetch the complaint
    result = await db.execute(
        select(Complaint).where(Complaint.id == uuid.UUID(complaint_id))
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    # Double-check current state matches expected from_state
    if complaint.status != from_state:
        raise ValueError(
            f"Complaint {complaint_id} is in state {complaint.status.value}, "
            f"expected {from_state.value}. Concurrent update may have occurred."
        )

    # Apply the state change
    complaint.status = to_state
    db.add(complaint)

    # Write to audit log
    # triggered_by is "system" or a user_id string. AuditLog.user_id is a UUID FK.
    # For system-triggered transitions we use the complaint's student_id as actor.
    if triggered_by == "system":
        actor_id = complaint.student_id
    else:
        try:
            actor_id = uuid.UUID(triggered_by)
        except ValueError:
            actor_id = complaint.student_id

    action_note = f" | {note}" if note else ""
    log_entry = AuditLog(
        user_id=actor_id,
        action=f"TRANSITION:{from_state.value}→{to_state.value}{action_note}",
        entity_type="complaint",
        entity_id=str(complaint_id),
        ip_address="0.0.0.0",  # Server-side action; no client IP
    )
    db.add(log_entry)
    await db.flush()

    logger.info(
        f"[transition_complaint] {complaint_id}: {from_state.value} → {to_state.value} "
        f"(triggered_by={triggered_by})"
    )
    return complaint


# ---------------------------------------------------------------------------
# create_complaint
# ---------------------------------------------------------------------------

async def create_complaint(
    student_id: str,
    data,  # ComplaintCreate schema
    db: AsyncSession,
) -> Complaint:
    """
    Creates a complaint in INTAKE state.
    Sanitizes text via prompt_sanitizer.
    Stores both original and sanitized text.
    Stores flagged_input if injection was detected.
    Does NOT classify — classification happens asynchronously in Celery.
    """
    sanitization = sanitize_input(data.text)

    complaint = Complaint(
        student_id=uuid.UUID(student_id),
        text=sanitization.original_text,
        sanitized_text=sanitization.sanitized_text,
        is_anonymous=data.is_anonymous,
        status=ComplaintStatus.INTAKE,
        flagged_input=sanitization.original_text if sanitization.was_flagged else None,
        classified_by=ClassifiedBy.fallback,  # Default; Celery task updates this
        requires_approval=False,
    )
    db.add(complaint)
    await db.flush()  # Get the UUID

    return complaint


# ---------------------------------------------------------------------------
# get_complaint — role-based access control
# ---------------------------------------------------------------------------

async def get_complaint(
    complaint_id: str,
    requesting_user_id: str,
    requesting_user_role: UserRole,
    db: AsyncSession,
) -> Complaint:
    """
    Fetches a complaint.
    Students can only access their own complaints (403 otherwise).
    Staff and wardens can access any complaint.
    Raises 404 if not found, 403 if not authorized.
    """
    result = await db.execute(
        select(Complaint).where(Complaint.id == uuid.UUID(complaint_id))
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    # Students can only see their own complaints
    staff_roles = {
        UserRole.laundry_man,
        UserRole.mess_secretary,
        UserRole.mess_manager,
        UserRole.assistant_warden,
        UserRole.warden,
        UserRole.chief_warden,
    }
    if requesting_user_role not in staff_roles:
        if str(complaint.student_id) != requesting_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this complaint.",
            )

    return complaint


# ---------------------------------------------------------------------------
# assign_complaint
# ---------------------------------------------------------------------------

async def assign_complaint(
    complaint_id: str,
    assignee_id: str,
    category: ComplaintCategory,
    severity: ComplaintSeverity,
    classified_by: str,  # "llm" or "fallback"
    db: AsyncSession,
) -> Complaint:
    """
    Assigns a complaint to a staff member.
    Calls transition_complaint() to move status to ASSIGNED.
    Never called directly for high-severity complaints.
    """
    result = await db.execute(
        select(Complaint).where(Complaint.id == uuid.UUID(complaint_id))
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    # Update classification fields
    complaint.category = category
    complaint.severity = severity
    complaint.assigned_to = uuid.UUID(assignee_id)
    complaint.classified_by = ClassifiedBy(classified_by)
    db.add(complaint)

    # Transition state: INTAKE or CLASSIFIED → ASSIGNED
    from_state = complaint.status
    if from_state not in (ComplaintStatus.INTAKE, ComplaintStatus.CLASSIFIED,
                          ComplaintStatus.AWAITING_APPROVAL, ComplaintStatus.REOPENED,
                          ComplaintStatus.ESCALATED):
        raise ValueError(
            f"Cannot assign complaint from state {from_state.value}."
        )

    # Normalise to CLASSIFIED for transition if still in INTAKE
    # (sprint prompt allows INTAKE → ASSIGNED via service, not via machine directly)
    if from_state == ComplaintStatus.INTAKE:
        complaint.status = ComplaintStatus.CLASSIFIED
        from_state = ComplaintStatus.CLASSIFIED

    await transition_complaint(
        complaint_id=complaint_id,
        from_state=from_state,
        to_state=ComplaintStatus.ASSIGNED,
        triggered_by="system",
        db=db,
        note=f"Assigned to {assignee_id} by {classified_by} classifier",
    )
    return complaint


# ---------------------------------------------------------------------------
# send_to_approval_queue
# ---------------------------------------------------------------------------

async def send_to_approval_queue(
    complaint_id: str,
    ai_category: ComplaintCategory,
    ai_severity: ComplaintSeverity,
    ai_assignee_id: str,
    confidence: float,
    db: AsyncSession,
) -> ApprovalQueueItem:
    """
    Creates an approval queue item and transitions the complaint to AWAITING_APPROVAL.
    ai_assignee_id must be a valid user UUID (the suggested staff member).
    If no suitable assignee is known, pass the warden's UUID instead.
    """
    result = await db.execute(
        select(Complaint).where(Complaint.id == uuid.UUID(complaint_id))
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    # Update AI suggestion fields on the complaint
    complaint.ai_suggested_category = ai_category
    complaint.ai_suggested_assignee = uuid.UUID(ai_assignee_id)
    complaint.confidence_score = confidence
    complaint.requires_approval = True
    db.add(complaint)

    # Create the approval queue item
    queue_item = ApprovalQueueItem(
        complaint_id=uuid.UUID(complaint_id),
        ai_suggested_category=ai_category,
        ai_suggested_severity=ai_severity,
        ai_suggested_assignee=uuid.UUID(ai_assignee_id),
        confidence_score=confidence,
    )
    db.add(queue_item)
    await db.flush()

    # Transition to AWAITING_APPROVAL
    from_state = complaint.status
    if from_state == ComplaintStatus.INTAKE:
        # Temporarily move to CLASSIFIED so the transition is valid
        complaint.status = ComplaintStatus.CLASSIFIED
        from_state = ComplaintStatus.CLASSIFIED

    await transition_complaint(
        complaint_id=complaint_id,
        from_state=from_state,
        to_state=ComplaintStatus.AWAITING_APPROVAL,
        triggered_by="system",
        db=db,
        note=f"Sent to approval queue (confidence={confidence:.2f})",
    )
    return queue_item


# ---------------------------------------------------------------------------
# Helper: find a warden to use as fallback assignee
# ---------------------------------------------------------------------------

async def get_fallback_warden_id(db: AsyncSession) -> Optional[uuid.UUID]:
    """
    Returns the UUID of any active assistant_warden or warden.
    Used when routing to approval queue and no specific assignee is known.
    Returns None if no warden exists (run create_admin.py first).
    """
    from models.user import User
    for role in (UserRole.assistant_warden, UserRole.warden, UserRole.chief_warden):
        result = await db.execute(
            select(User).where(User.role == role, User.is_active == True)  # noqa: E712
        )
        user = result.scalars().first()
        if user:
            return user.id
    return None
