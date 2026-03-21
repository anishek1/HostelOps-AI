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
    ip_address: str = "0.0.0.0",
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
        ip_address=ip_address,
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
    ip_address: str = "0.0.0.0",
) -> Complaint:
    """
    Creates a complaint in INTAKE state.
    Sanitizes text via prompt_sanitizer.
    Stores both original and sanitized text.
    Stores flagged_input if injection was detected.
    Does NOT classify — classification happens asynchronously in Celery.
    """
    sanitization = sanitize_input(data.text)

    # Sprint 7: Inherit hostel_id from the student record
    from models.user import User
    student = await db.get(User, uuid.UUID(student_id))
    hostel_id = student.hostel_id if student else None

    complaint = Complaint(
        student_id=uuid.UUID(student_id),
        text=sanitization.original_text,
        sanitized_text=sanitization.sanitized_text,
        is_anonymous=data.is_anonymous,
        status=ComplaintStatus.INTAKE,
        flagged_input=sanitization.original_text if sanitization.was_flagged else None,
        classified_by=ClassifiedBy.fallback,  # Default; Celery task updates this
        requires_approval=False,
        hostel_id=hostel_id,  # Sprint 7
    )
    db.add(complaint)
    await db.flush()  # Get the UUID
    
    log_entry = AuditLog(
        user_id=uuid.UUID(student_id),
        action="COMPLAINT_CREATED",
        entity_type="complaint",
        entity_id=str(complaint.id),
        ip_address=ip_address,
    )
    db.add(log_entry)
    await db.flush()

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
        await transition_complaint(
            complaint_id=complaint_id,
            from_state=ComplaintStatus.INTAKE,
            to_state=ComplaintStatus.CLASSIFIED,
            triggered_by="system",
            db=db,
            note="Auto-classified before assignment",
        )
        from_state = ComplaintStatus.CLASSIFIED

    await transition_complaint(
        complaint_id=complaint_id,
        from_state=from_state,
        to_state=ComplaintStatus.ASSIGNED,
        triggered_by="system",
        db=db,
        note=f"Assigned to {assignee_id} by {classified_by} classifier",
    )
    await db.commit()
    await db.refresh(complaint)
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
        await transition_complaint(
            complaint_id=complaint_id,
            from_state=ComplaintStatus.INTAKE,
            to_state=ComplaintStatus.CLASSIFIED,
            triggered_by="system",
            db=db,
            note="Auto-classified before approval queue",
        )
        from_state = ComplaintStatus.CLASSIFIED

    await transition_complaint(
        complaint_id=complaint_id,
        from_state=from_state,
        to_state=ComplaintStatus.AWAITING_APPROVAL,
        triggered_by="system",
        db=db,
        note=f"Sent to approval queue (confidence={confidence:.2f})",
    )
    await db.commit()
    await db.refresh(queue_item)
    return queue_item


# ---------------------------------------------------------------------------
# Helper: find a warden to use as fallback assignee
# ---------------------------------------------------------------------------

async def get_fallback_warden_id(db: AsyncSession, hostel_id=None) -> Optional[uuid.UUID]:
    """
    Returns the UUID of any active assistant_warden or warden.
    Sprint 7: Scoped to hostel_id when provided.
    Used when routing to approval queue and no specific assignee is known.
    Returns None if no warden exists (run create_admin.py first).
    """
    from models.user import User
    for role in (UserRole.assistant_warden, UserRole.warden, UserRole.chief_warden):
        query = select(User).where(User.role == role, User.is_active == True)  # noqa: E712
        if hostel_id is not None:
            query = query.where(User.hostel_id == hostel_id)
        result = await db.execute(query)
        user = result.scalars().first()
        if user:
            return user.id
    return None


# ---------------------------------------------------------------------------
# Sprint 3: staff_update_progress
# ---------------------------------------------------------------------------


async def staff_update_progress(
    complaint_id: str,
    new_status: ComplaintStatus,
    staff_id: str,
    db: AsyncSession,
    ip_address: str = "0.0.0.0",
) -> Complaint:
    """
    Staff updates complaint progress:
    ASSIGNED → IN_PROGRESS or IN_PROGRESS → RESOLVED.
    Staff must be the assigned person.
    """
    from services.notification_service import notify_user

    result = await db.execute(
        select(Complaint).where(Complaint.id == uuid.UUID(complaint_id))
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    # Verify staff is the assigned person
    if str(complaint.assigned_to) != staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this complaint.",
        )

    # Validate allowed transitions
    valid_staff_transitions = {
        ComplaintStatus.ASSIGNED: ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.IN_PROGRESS: ComplaintStatus.RESOLVED,
    }
    expected = valid_staff_transitions.get(complaint.status)
    if expected is None or expected != new_status:
        raise ValueError(
            f"Invalid status update: {complaint.status.value} → {new_status.value}. "
            f"Staff can only move ASSIGNED→IN_PROGRESS or IN_PROGRESS→RESOLVED."
        )

    # Transition
    updated = await transition_complaint(
        complaint_id=complaint_id,
        from_state=complaint.status,
        to_state=new_status,
        triggered_by=staff_id,
        db=db,
        note=f"Progress update by staff {staff_id}",
        ip_address=ip_address,
    )

    # If resolved, notify student
    if new_status == ComplaintStatus.RESOLVED and not complaint.is_anonymous:
        try:
            await notify_user(
                recipient_id=complaint.student_id,
                title="Complaint Resolved",
                body=(
                    f"Your complaint {str(complaint.id)[:8].upper()} has been marked as resolved. "
                    f"Please confirm or reopen if needed."
                ),
                notification_type=NotificationType.complaint_resolved,
                db=db,
            )
        except Exception:
            pass  # Notification failure is non-critical

    logger.info(f"[staff_update_progress] {complaint_id}: → {new_status.value} by {staff_id}")
    await db.commit()
    await db.refresh(updated)
    return updated


# ---------------------------------------------------------------------------
# Sprint 3: student_confirm_resolution
# ---------------------------------------------------------------------------


async def student_confirm_resolution(
    complaint_id: str,
    student_id: str,
    db: AsyncSession,
    ip_address: str = "0.0.0.0",
) -> Complaint:
    """
    Student confirms that a resolved complaint is satisfactorily resolved.
    Sets resolved_confirmed_at timestamp.
    """
    from datetime import datetime, timezone

    result = await db.execute(
        select(Complaint).where(Complaint.id == uuid.UUID(complaint_id))
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    if str(complaint.student_id) != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this complaint.",
        )

    if complaint.status != ComplaintStatus.RESOLVED:
        raise ValueError("Complaint is not in RESOLVED state.")

    complaint.resolved_confirmed_at = datetime.now(timezone.utc)
    db.add(complaint)
    
    # Write to audit log since this changes state meaningfully
    log_entry = AuditLog(
        user_id=uuid.UUID(student_id),
        action="RESOLUTION_CONFIRMED",
        entity_type="complaint",
        entity_id=str(complaint_id),
        ip_address=ip_address,
    )
    db.add(log_entry)
    await db.flush()

    logger.info(f"[student_confirm_resolution] {complaint_id}: confirmed by {student_id}")
    await db.commit()
    await db.refresh(complaint)
    return complaint


# ---------------------------------------------------------------------------
# Sprint 3: student_reopen_complaint
# ---------------------------------------------------------------------------


async def student_reopen_complaint(
    complaint_id: str,
    student_id: str,
    reopen_reason: str,
    db: AsyncSession,
    ip_address: str = "0.0.0.0",
) -> Complaint:
    """
    Student reopens a resolved complaint with a reason.
    Sets is_priority=True and transitions to REOPENED.
    Notifies assistant wardens.
    """
    from services.notification_service import notify_all_by_role

    result = await db.execute(
        select(Complaint).where(Complaint.id == uuid.UUID(complaint_id))
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    if str(complaint.student_id) != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reopen your own complaints.",
        )

    if complaint.status != ComplaintStatus.RESOLVED:
        raise ValueError("Only resolved complaints can be reopened.")

    # Transition to REOPENED
    await transition_complaint(
        complaint_id=complaint_id,
        from_state=ComplaintStatus.RESOLVED,
        to_state=ComplaintStatus.REOPENED,
        triggered_by=student_id,
        db=db,
        note=f"Reopened by student — reason: {reopen_reason}",
        ip_address=ip_address,
    )

    complaint.reopen_reason = reopen_reason
    complaint.is_priority = True
    db.add(complaint)
    await db.flush()

    # Notify assistant wardens
    try:
        await notify_all_by_role(
            role=UserRole.assistant_warden,
            title="Complaint Reopened",
            body=(
                f"Complaint {str(complaint.id)[:8].upper()} has been reopened. "
                f"Reason: {reopen_reason}"
            ),
            notification_type=NotificationType.complaint_reopened,
            db=db,
            hostel_id=complaint.hostel_id,
        )
    except Exception:
        pass  # Notification failure is non-critical

    logger.info(f"[student_reopen_complaint] {complaint_id}: reopened by {student_id}")
    await db.commit()
    await db.refresh(complaint)
    return complaint


# ---------------------------------------------------------------------------
# Sprint 3: get_my_complaints
# ---------------------------------------------------------------------------


async def get_my_complaints(
    student_id: str,
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> list[Complaint]:
    """Returns complaints filed by a student, newest first, paginated."""
    result = await db.execute(
        select(Complaint)
        .where(Complaint.student_id == uuid.UUID(student_id))
        .order_by(Complaint.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


async def list_complaints(
    db: AsyncSession,
    hostel_id=None,
    complaint_status: Optional[ComplaintStatus] = None,
    category: Optional[ComplaintCategory] = None,
    severity: Optional[ComplaintSeverity] = None,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Complaint]:
    """
    Returns complaints for a hostel with optional filters, newest first.
    Golden Rule 31: always scoped by hostel_id when provided.
    """
    query = select(Complaint).order_by(Complaint.created_at.desc())

    if hostel_id is not None:
        query = query.where(Complaint.hostel_id == hostel_id)
    if complaint_status is not None:
        query = query.where(Complaint.status == complaint_status)
    if category is not None:
        query = query.where(Complaint.category == category)
    if severity is not None:
        query = query.where(Complaint.severity == severity)
    if search:
        query = query.where(Complaint.text.ilike(f"%{search}%"))

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
