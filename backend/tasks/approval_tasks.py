"""
tasks/approval_tasks.py — HostelOps AI
=========================================
Background tasks for approval queue management.
Auto-escalates stale pending items using the same sync DB pattern as complaint_tasks.py.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone

from celery_app import celery_app
from config import settings
from database import SyncSessionLocal
from schemas.enums import (
    ApprovalStatus,
    ComplaintStatus,
    NotificationType,
    UserRole,
)
from services.complaint_service import VALID_TRANSITIONS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sync helpers (same pattern as complaint_tasks.py)
# ---------------------------------------------------------------------------


def _transition_complaint_sync(
    complaint_id: str,
    from_state: ComplaintStatus,
    to_state: ComplaintStatus,
    triggered_by: str,
    session,
    note: str = "",
):
    """Sync version of transition_complaint for Celery tasks."""
    from sqlalchemy import select
    from models.complaint import Complaint
    from models.audit_log import AuditLog

    allowed = VALID_TRANSITIONS.get(from_state, [])
    if to_state not in allowed:
        raise ValueError(f"Invalid transition: {from_state.value} → {to_state.value}")

    complaint = session.execute(
        select(Complaint).where(Complaint.id == uuid.UUID(complaint_id))
    ).scalar_one_or_none()
    if not complaint:
        raise ValueError(f"Complaint {complaint_id} not found")

    complaint.status = to_state
    actor_id = complaint.student_id
    action_note = f" | {note}" if note else ""
    log_entry = AuditLog(
        user_id=actor_id,
        action=f"TRANSITION:{from_state.value}→{to_state.value}{action_note}",
        entity_type="complaint",
        entity_id=str(complaint_id),
        ip_address="0.0.0.0",
    )
    session.add(log_entry)
    session.flush()
    return complaint


def _create_notification_sync(recipient_id, title, body, notification_type, session):
    """Write a notification record synchronously."""
    from models.notification import Notification
    notification = Notification(
        recipient_id=recipient_id,
        title=title,
        body=body,
        type=notification_type,
    )
    session.add(notification)
    session.flush()


# ---------------------------------------------------------------------------
# Celery task: check_approval_timeouts
# ---------------------------------------------------------------------------


@celery_app.task(name="tasks.approval_tasks.check_approval_timeouts")
def check_approval_timeouts():
    """
    Auto-escalate complaints that have been pending approval for too long.
    Runs every 15 minutes via Celery beat schedule.
    Timeout is configured via APPROVAL_QUEUE_TIMEOUT_MINUTES in settings.
    """
    timeout_minutes = settings.APPROVAL_QUEUE_TIMEOUT_MINUTES
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

    logger.info(
        f"[approval_timeout] Checking for stale pending items "
        f"(cutoff: {cutoff.isoformat()}, timeout: {timeout_minutes}min)"
    )

    with SyncSessionLocal() as session:
        try:
            from sqlalchemy import select
            from models.approval_queue import ApprovalQueueItem
            from models.complaint import Complaint

            # Find pending items older than cutoff
            result = session.execute(
                select(ApprovalQueueItem)
                .where(ApprovalQueueItem.status == ApprovalStatus.pending)
                .where(ApprovalQueueItem.created_at < cutoff)
            )
            items = result.scalars().all()

            if not items:
                logger.info("[approval_timeout] No stale items found")
                return {"status": "ok", "escalated": 0}

            escalated_count = 0
            for item in items:
                complaint = session.execute(
                    select(Complaint).where(Complaint.id == item.complaint_id)
                ).scalar_one_or_none()
                if not complaint:
                    logger.error(
                        f"[approval_timeout] Complaint {item.complaint_id} not found "
                        f"for timeout item {item.id}"
                    )
                    continue

                try:
                    # Transition to ESCALATED
                    _transition_complaint_sync(
                        complaint_id=str(complaint.id),
                        from_state=complaint.status,
                        to_state=ComplaintStatus.ESCALATED,
                        triggered_by="system:timeout",
                        session=session,
                        note=f"Auto-escalated — approval timeout ({timeout_minutes}min)",
                    )

                    # Update queue item status
                    item.status = ApprovalStatus.timed_out
                    session.flush()

                    # Notify wardens about the timeout
                    from models.user import User
                    wardens = session.execute(
                        select(User).where(
                            User.role.in_([UserRole.warden, UserRole.chief_warden]),
                            User.is_active == True,  # noqa: E712
                        )
                    ).scalars().all()
                    for warden in wardens:
                        _create_notification_sync(
                            recipient_id=warden.id,
                            title="Approval Timeout",
                            body=(
                                f"Complaint {str(complaint.id)[:8].upper()} "
                                f"auto-escalated due to approval timeout."
                            ),
                            notification_type=NotificationType.complaint_escalated,
                            session=session,
                        )

                    escalated_count += 1
                    logger.info(
                        f"[approval_timeout] Auto-escalated complaint {complaint.id} "
                        f"(queue item {item.id})"
                    )

                except Exception as e:
                    logger.error(
                        f"[approval_timeout] Failed to auto-escalate complaint "
                        f"{complaint.id}: {e}"
                    )
                    session.rollback()
                    continue

            session.commit()
            logger.info(
                f"[approval_timeout] Completed — {escalated_count} complaints escalated"
            )
            return {"status": "ok", "escalated": escalated_count}

        except Exception as exc:
            session.rollback()
            logger.error(f"[approval_timeout] Unhandled error: {exc}", exc_info=True)
            raise
