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
logger = logging.getLogger(__name__)

# Import shared sync helpers from complaint_tasks to avoid duplication (Fix 12)
from tasks.complaint_tasks import _transition_complaint_sync, _create_notification_sync  # noqa: E402


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

                    # Notify wardens about the timeout — scoped to complaint's hostel
                    from models.user import User
                    warden_q = select(User).where(
                        User.role.in_([UserRole.warden, UserRole.chief_warden]),
                        User.is_active == True,  # noqa: E712
                    )
                    if complaint.hostel_id is not None:
                        warden_q = warden_q.where(User.hostel_id == complaint.hostel_id)
                    wardens = session.execute(warden_q).scalars().all()
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
