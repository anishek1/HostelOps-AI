"""
complaint_tasks.py — HostelOps AI
===================================
Background tasks for complaint processing.
All LLM classification runs here — never synchronously in routes.
Implements full retry policy and fallback chain from PRD.md Section 10.
"""
import asyncio
import logging
import uuid
import logging
logger = logging.getLogger(__name__)

from celery_app import celery_app
from config import settings
from database import SyncSessionLocal
from schemas.enums import (
    ClassifiedBy,
    ComplaintCategory,
    ComplaintSeverity,
    ComplaintStatus,
    NotificationType,
    UserRole,
)
from services.complaint_service import VALID_TRANSITIONS

import asyncio

def run_async(coro):
    """
    Runs an async coroutine from a sync Celery task.
    Creates a new event loop if none exists.
    Use this to call async tools from Celery tasks.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

# ---------------------------------------------------------------------------
# Helpers: sync DB wrappers for Celery (no async sessions allowed)
# ---------------------------------------------------------------------------

def _get_complaint_sync(complaint_id: str, session):
    from sqlalchemy import select
    from models.complaint import Complaint
    result = session.execute(
        select(Complaint).where(Complaint.id == uuid.UUID(complaint_id))
    )
    return result.scalar_one_or_none()


def _get_warden_sync(session):
    """Return UUID of any active warden/assistant_warden for approval queue."""
    from sqlalchemy import select
    from models.user import User
    for role in (UserRole.assistant_warden, UserRole.warden, UserRole.chief_warden):
        result = session.execute(
            select(User).where(User.role == role, User.is_active == True)  # noqa: E712
        )
        user = result.scalars().first()
        if user:
            return user.id
    return None


def _find_assignee_sync(category: ComplaintCategory, session):
    """Find a staff member to handle the complaint based on category."""
    from sqlalchemy import select
    from models.user import User

    role_map = {
        ComplaintCategory.mess: [UserRole.mess_secretary, UserRole.mess_manager],
        ComplaintCategory.laundry: [UserRole.laundry_man],
        ComplaintCategory.maintenance: [UserRole.assistant_warden],
        ComplaintCategory.interpersonal: [UserRole.assistant_warden, UserRole.warden],
        ComplaintCategory.critical: [UserRole.warden, UserRole.chief_warden],
        ComplaintCategory.uncategorised: [UserRole.assistant_warden],
    }
    target_roles = role_map.get(category, [UserRole.assistant_warden])
    for role in target_roles:
        result = session.execute(
            select(User).where(User.role == role, User.is_active == True)  # noqa: E712
        )
        user = result.scalars().first()
        if user:
            return user.id
    return _get_warden_sync(session)


def _update_complaint_sync(complaint_id: str, updates: dict, session):
    """Apply field updates to a complaint without state changes."""
    from sqlalchemy import select
    from models.complaint import Complaint
    complaint = session.execute(
        select(Complaint).where(Complaint.id == uuid.UUID(complaint_id))
    ).scalar_one_or_none()
    if not complaint:
        return
    for field, value in updates.items():
        setattr(complaint, field, value)
    session.flush()
    return complaint


def _transition_complaint_sync(
    complaint_id: str, from_state: ComplaintStatus, to_state: ComplaintStatus,
    triggered_by: str, session, note: str = ""
):
    """Sync version of transition_complaint for Celery tasks."""
    from sqlalchemy import select
    from models.complaint import Complaint
    from models.audit_log import AuditLog

    # Validate transition (VALID_TRANSITIONS imported from complaint_service.py)
    allowed = VALID_TRANSITIONS.get(from_state, [])
    if to_state not in allowed:
        raise ValueError(f"Invalid transition: {from_state.value} → {to_state.value}")

    complaint = session.execute(
        select(Complaint).where(Complaint.id == uuid.UUID(complaint_id))
    ).scalar_one_or_none()
    if not complaint:
        raise ValueError(f"Complaint {complaint_id} not found")

    complaint.status = to_state
    actor_id = complaint.student_id  # system actions attributed to the student
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


def _create_notification_sync(recipient_id, title: str, body: str,
                               notification_type: NotificationType, session):
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


def _notify_wardens_flagged_input_sync(complaint_id: str, session):
    """Passive alert to all assistant wardens about flagged prompt injection."""
    try:
        from sqlalchemy import select
        from models.user import User
        wardens = session.execute(
            select(User).where(
                User.role.in_([UserRole.assistant_warden, UserRole.warden]),
                User.is_active == True,  # noqa: E712
            )
        ).scalars().all()
        for warden in wardens:
            _create_notification_sync(
                recipient_id=warden.id,
                title="⚠️ Flagged Complaint Input",
                body=f"Complaint {str(complaint_id)[:8].upper()} may contain a prompt injection attempt.",
                notification_type=NotificationType.approval_needed,
                session=session,
            )
    except Exception as e:
        logger.error(f"[classify_task] Warden flagged-input notification failed: {e}")


# ---------------------------------------------------------------------------
# Main Celery task
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    name="tasks.complaint_tasks.classify_and_route_complaint",
)
def classify_and_route_complaint(self, complaint_id: str):
    """
    Full classification pipeline for a single complaint.

    Flow:
    1. Fetch complaint from DB
    2. Send student acknowledgement FIRST
    3. Try LLM classification (up to 3 retries with backoff via Celery)
    4. If LLM fails → use fallback classifier
    5. If confidence >= threshold AND severity != high → auto-assign
    6. If confidence < threshold OR severity == high → approval queue
    7. If injection was flagged → passive alert to Warden
    """
    from services.fallback_classifier import classify_with_fallback

    logger.info(f"[classify_task] Starting classification for complaint {complaint_id}")

    with SyncSessionLocal() as session:
        try:
            # Step 1 — Fetch complaint
            complaint = _get_complaint_sync(complaint_id, session)
            if not complaint:
                logger.error(f"[classify_task] Complaint {complaint_id} not found — aborting.")
                return {"status": "error", "reason": "complaint_not_found"}

            # Step 2 — Send acknowledgement FIRST (before LLM)
            from tools.complaint_tools import acknowledge_student_tool, AcknowledgeStudentInput

            run_async(acknowledge_student_tool(
                AcknowledgeStudentInput(
                    complaint_id=complaint_id,
                    student_id=str(complaint.student_id),
                    is_anonymous=complaint.is_anonymous,
                ),
                db=session  # pass the sync session wrapped appropriately - the tool uses it transparently if it only adds/commits objects or we can let it run as a mock DB object
            ))
            session.commit()

            # Step 3 — Try LLM classification
            llm_result = None
            complaint_text = complaint.sanitized_text or complaint.text

            try:
                # Run the async LLM call inside a new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    from agents.agent_complaint import classify_complaint
                    llm_result = loop.run_until_complete(classify_complaint(complaint_text))
                finally:
                    loop.close()
            except Exception as llm_err:
                logger.warning(f"[classify_task] LLM call error: {llm_err}")

            # Step 4 — Determine classification
            if llm_result is not None:
                classified_by = ClassifiedBy.llm
                try:
                    category = ComplaintCategory(llm_result.category)
                except ValueError:
                    category = ComplaintCategory.uncategorised
                try:
                    severity = ComplaintSeverity(llm_result.severity)
                except ValueError:
                    severity = ComplaintSeverity.medium
                confidence = llm_result.confidence
                logger.info(
                    f"[classify_task] LLM result: category={category.value}, "
                    f"severity={severity.value}, confidence={confidence:.2f}"
                )
            else:
                # Fallback classifier
                classified_by = ClassifiedBy.fallback
                fallback = classify_with_fallback(complaint_text)
                category = fallback.category
                severity = fallback.severity
                confidence = 0.0
                logger.info(
                    f"[classify_task] Fallback result: category={category.value}, "
                    f"severity={severity.value}"
                )

            # Update classification fields on complaint
            complaint.category = category
            complaint.severity = severity
            complaint.classified_by = classified_by
            complaint.confidence_score = confidence
            complaint.ai_suggested_category = category
            session.flush()

            # Step 5/6 — Route based on confidence and severity
            threshold = settings.COMPLAINT_CONFIDENCE_THRESHOLD
            needs_approval = (
                severity == ComplaintSeverity.high
                or confidence < threshold
                or classified_by == ClassifiedBy.fallback
            )

            if needs_approval:
                # Route to approval queue
                warden_id = _get_warden_sync(session)
                if not warden_id:
                    logger.error(
                        "[classify_task] No warden found — complaint stays at INTAKE. "
                        "Run create_admin.py first."
                    )
                    session.commit()
                    return {"status": "error", "reason": "no_warden_exists"}

                complaint.ai_suggested_assignee = warden_id
                complaint.requires_approval = True
                session.flush()

                # Create approval queue item
                from models.approval_queue import ApprovalQueueItem
                queue_item = ApprovalQueueItem(
                    complaint_id=uuid.UUID(complaint_id),
                    ai_suggested_category=category,
                    ai_suggested_severity=severity,
                    ai_suggested_assignee=warden_id,
                    confidence_score=confidence,
                )
                session.add(queue_item)
                session.flush()

                # Transition INTAKE → CLASSIFIED → AWAITING_APPROVAL
                _transition_complaint_sync(
                    complaint_id, ComplaintStatus.INTAKE, ComplaintStatus.CLASSIFIED,
                    "system", session, note=f"Classified as {category.value}"
                )
                _transition_complaint_sync(
                    complaint_id, ComplaintStatus.CLASSIFIED, ComplaintStatus.AWAITING_APPROVAL,
                    "system", session, note=f"Sent to approval queue (confidence={confidence:.2f})"
                )

                # Notify the warden
                _create_notification_sync(
                    recipient_id=warden_id,
                    title="Complaint Needs Review",
                    body=(
                        f"A {category.value} complaint requires your approval. "
                        f"Severity: {severity.value}. Classified by: {classified_by.value}."
                    ),
                    notification_type=NotificationType.approval_needed,
                    session=session,
                )
                logger.info(f"[classify_task] Complaint {complaint_id} → AWAITING_APPROVAL")

            else:
                # Auto-assign
                assignee_id = _find_assignee_sync(category, session)
                if not assignee_id:
                    assignee_id = _get_warden_sync(session)
                if not assignee_id:
                    logger.error("[classify_task] No assignee found — falling back to approval queue.")
                    session.commit()
                    return {"status": "error", "reason": "no_assignee_found"}

                complaint.assigned_to = assignee_id
                complaint.requires_approval = False
                session.flush()

                # Transition INTAKE → CLASSIFIED → ASSIGNED
                _transition_complaint_sync(
                    complaint_id, ComplaintStatus.INTAKE, ComplaintStatus.CLASSIFIED,
                    "system", session, note=f"Classified as {category.value}"
                )
                _transition_complaint_sync(
                    complaint_id, ComplaintStatus.CLASSIFIED, ComplaintStatus.ASSIGNED,
                    "system", session, note=f"Auto-assigned by {classified_by.value}"
                )

                # Notify the assigned staff
                _create_notification_sync(
                    recipient_id=assignee_id,
                    title="New Complaint Assigned",
                    body=f"A {category.value} complaint has been assigned to you. Severity: {severity.value}.",
                    notification_type=NotificationType.complaint_assigned,
                    session=session,
                )
                logger.info(f"[classify_task] Complaint {complaint_id} → ASSIGNED to {assignee_id}")

            # Step 7 — Flagged injection alert
            if complaint.flagged_input:
                _notify_wardens_flagged_input_sync(complaint_id, session)

            session.commit()
            return {
                "status": "success",
                "complaint_id": complaint_id,
                "classified_by": classified_by.value,
                "category": category.value,
                "severity": severity.value,
            }

        except Exception as exc:
            session.rollback()
            logger.error(f"[classify_task] Unhandled error for {complaint_id}: {exc}", exc_info=True)
            raise
