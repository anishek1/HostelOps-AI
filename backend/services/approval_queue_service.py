"""
services/approval_queue_service.py — HostelOps AI
====================================================
Business logic for the warden approval queue:
approve, override, escalate.
All DB mutations go through this service — never directly from routes.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.approval_queue import ApprovalQueueItem
from models.complaint import Complaint
from schemas.enums import (
    ApprovalStatus,
    ClassifiedBy,
    ComplaintCategory,
    ComplaintSeverity,
    ComplaintStatus,
    NotificationType,
    OverrideReason,
    UserRole,
)
from services.complaint_service import transition_complaint
from services.notification_service import notify_all_by_role, notify_user
from services.override_log_service import create_override_log

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# get_pending_approvals
# ---------------------------------------------------------------------------


async def get_pending_approvals(db: AsyncSession) -> List[ApprovalQueueItem]:
    """
    Returns all pending approval queue items sorted by created_at ascending.
    """
    result = await db.execute(
        select(ApprovalQueueItem)
        .where(ApprovalQueueItem.status == ApprovalStatus.pending)
        .order_by(ApprovalQueueItem.created_at.asc())
    )
    items = result.scalars().all()
    logger.info(f"[approval_queue] Found {len(items)} pending items")
    return items


# ---------------------------------------------------------------------------
# approve_ai_suggestion
# ---------------------------------------------------------------------------


async def approve_ai_suggestion(
    queue_item_id: str,
    warden_id: str,
    db: AsyncSession,
    ip_address: str = "0.0.0.0",
) -> Complaint:
    """
    Warden approves the AI suggestion as-is.
    Transitions complaint AWAITING_APPROVAL → ASSIGNED.
    """
    item = await db.get(ApprovalQueueItem, uuid.UUID(queue_item_id))
    if not item or item.status != ApprovalStatus.pending:
        raise ValueError("Approval item not found or not pending")

    complaint = await db.get(Complaint, item.complaint_id)
    if not complaint:
        raise ValueError("Associated complaint not found")

    # Update queue item
    item.status = ApprovalStatus.approved
    item.reviewed_by = uuid.UUID(warden_id)
    item.reviewed_at = datetime.now(timezone.utc)
    db.add(item)

    # Assign complaint using AI's suggestion
    complaint.category = item.ai_suggested_category
    complaint.severity = item.ai_suggested_severity
    complaint.assigned_to = item.ai_suggested_assignee
    complaint.requires_approval = False
    db.add(complaint)

    # Transition to ASSIGNED
    await transition_complaint(
        complaint_id=str(complaint.id),
        from_state=ComplaintStatus.AWAITING_APPROVAL,
        to_state=ComplaintStatus.ASSIGNED,
        triggered_by=warden_id,
        db=db,
        note="Approved by warden — AI suggestion accepted",
        ip_address=ip_address,
    )

    # Notify assigned staff
    await notify_user(
        recipient_id=item.ai_suggested_assignee,
        title="New Complaint Assigned",
        body=f"Complaint {str(complaint.id)[:8].upper()} has been assigned to you.",
        notification_type=NotificationType.complaint_assigned,
        db=db,
    )

    # Notify student if not anonymous
    if not complaint.is_anonymous:
        await notify_user(
            recipient_id=complaint.student_id,
            title="Complaint Reviewed",
            body=f"Your complaint {str(complaint.id)[:8].upper()} has been reviewed and assigned.",
            notification_type=NotificationType.complaint_assigned,
            db=db,
        )

    logger.info(
        f"[approval_queue] Approved AI suggestion for complaint {complaint.id} "
        f"by warden {warden_id}"
    )
    await db.refresh(complaint)
    return complaint


# ---------------------------------------------------------------------------
# override_ai_suggestion
# ---------------------------------------------------------------------------


async def override_ai_suggestion(
    queue_item_id: str,
    warden_id: str,
    corrected_category: ComplaintCategory,
    corrected_severity: ComplaintSeverity,
    corrected_assignee_id: str,
    reason: OverrideReason,
    db: AsyncSession,
    ip_address: str = "0.0.0.0",
) -> Complaint:
    """
    Warden overrides the AI suggestion with corrected values.
    Logs the override reason.
    """
    item = await db.get(ApprovalQueueItem, uuid.UUID(queue_item_id))
    if not item or item.status != ApprovalStatus.pending:
        raise ValueError("Approval item not found or not pending")

    complaint = await db.get(Complaint, item.complaint_id)
    if not complaint:
        raise ValueError("Associated complaint not found")

    # Update queue item
    item.status = ApprovalStatus.corrected
    item.reviewed_by = uuid.UUID(warden_id)
    item.reviewed_at = datetime.now(timezone.utc)
    item.override_reason = reason.value
    db.add(item)

    # Log override details
    logger.info(
        f"[approval_queue] Override: complaint {complaint.id}, reason: {reason.value}, "
        f"original: category={item.ai_suggested_category}, severity={item.ai_suggested_severity}, "
        f"corrected: category={corrected_category}, severity={corrected_severity}, "
        f"assignee={corrected_assignee_id}"
    )

    # Log the override to the database
    await create_override_log(
        complaint_id=str(complaint.id),
        warden_id=warden_id,
        original_category=item.ai_suggested_category,
        corrected_category=corrected_category,
        original_severity=item.ai_suggested_severity,
        corrected_severity=corrected_severity,
        original_assignee=str(item.ai_suggested_assignee) if item.ai_suggested_assignee else None,
        corrected_assignee=corrected_assignee_id,
        reason=reason,
        db=db
    )

    # Assign with corrected values
    complaint.category = corrected_category
    complaint.severity = corrected_severity
    complaint.assigned_to = uuid.UUID(corrected_assignee_id)
    complaint.classified_by = ClassifiedBy.warden_override
    complaint.override_reason = reason
    complaint.requires_approval = False
    db.add(complaint)

    # Transition to ASSIGNED
    await transition_complaint(
        complaint_id=str(complaint.id),
        from_state=ComplaintStatus.AWAITING_APPROVAL,
        to_state=ComplaintStatus.ASSIGNED,
        triggered_by=warden_id,
        db=db,
        note=f"Overridden by warden — reason: {reason.value}",
        ip_address=ip_address,
    )

    # Notify assigned staff
    await notify_user(
        recipient_id=uuid.UUID(corrected_assignee_id),
        title="New Complaint Assigned",
        body=f"Complaint {str(complaint.id)[:8].upper()} (overridden) has been assigned to you.",
        notification_type=NotificationType.complaint_assigned,
        db=db,
    )

    # Notify student if not anonymous
    if not complaint.is_anonymous:
        await notify_user(
            recipient_id=complaint.student_id,
            title="Complaint Reviewed",
            body=f"Your complaint {str(complaint.id)[:8].upper()} has been reviewed and assigned.",
            notification_type=NotificationType.complaint_assigned,
            db=db,
        )

    await db.refresh(complaint)
    return complaint


# ---------------------------------------------------------------------------
# escalate_complaint
# ---------------------------------------------------------------------------


async def escalate_complaint(
    complaint_id: str,
    warden_id: str,
    reason: str,
    db: AsyncSession,
    ip_address: str = "0.0.0.0",
) -> Complaint:
    """
    Escalate a complaint to chief warden.
    Can be called from any pre-resolution state.
    """
    complaint = await db.get(Complaint, uuid.UUID(complaint_id))
    if not complaint:
        raise ValueError("Complaint not found")

    # Transition to ESCALATED
    await transition_complaint(
        complaint_id=complaint_id,
        from_state=complaint.status,
        to_state=ComplaintStatus.ESCALATED,
        triggered_by=warden_id,
        db=db,
        note=f"Escalated by warden — reason: {reason}",
        ip_address=ip_address,
    )

    # Notify all chief wardens
    await notify_all_by_role(
        role=UserRole.chief_warden,
        title="Complaint Escalated",
        body=(
            f"Complaint {str(complaint.id)[:8].upper()} has been escalated. "
            f"Reason: {reason}"
        ),
        notification_type=NotificationType.complaint_escalated,
        db=db,
    )

    # Notify student if not anonymous
    if not complaint.is_anonymous:
        await notify_user(
            recipient_id=complaint.student_id,
            title="Complaint Escalated",
            body=f"Your complaint {str(complaint.id)[:8].upper()} has been escalated to chief warden.",
            notification_type=NotificationType.complaint_escalated,
            db=db,
        )

    logger.info(f"[approval_queue] Escalated complaint {complaint_id} by warden {warden_id}")
    await db.refresh(complaint)
    return complaint
