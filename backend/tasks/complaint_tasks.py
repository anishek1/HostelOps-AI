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

logger = logging.getLogger(__name__)

from celery_app import celery_app
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


def _get_warden_sync(session, hostel_id=None):
    """Return UUID of any active warden for approval queue, scoped to hostel."""
    from sqlalchemy import select
    from models.user import User
    for role in (UserRole.warden,):
        q = select(User).where(User.role == role, User.is_active == True)  # noqa: E712
        if hostel_id is not None:
            q = q.where(User.hostel_id == hostel_id)
        result = session.execute(q)
        user = result.scalars().first()
        if user:
            return user.id
    return None


def _find_assignee_sync(category: ComplaintCategory, session, hostel_id=None):
    """Find a staff member to handle the complaint based on category, scoped to hostel."""
    from sqlalchemy import select
    from models.user import User

    role_map = {
        ComplaintCategory.mess: [UserRole.mess_staff],
        ComplaintCategory.laundry: [UserRole.laundry_man],
        ComplaintCategory.maintenance: [UserRole.warden],
        ComplaintCategory.interpersonal: [UserRole.warden],
        ComplaintCategory.critical: [UserRole.warden],
        ComplaintCategory.uncategorised: [UserRole.warden],
    }
    target_roles = role_map.get(category, [UserRole.warden])
    for role in target_roles:
        q = select(User).where(User.role == role, User.is_active == True)  # noqa: E712
        if hostel_id is not None:
            q = q.where(User.hostel_id == hostel_id)
        result = session.execute(q)
        user = result.scalars().first()
        if user:
            return user.id
    return _get_warden_sync(session, hostel_id=hostel_id)


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


def _notify_wardens_flagged_input_sync(complaint_id: str, session, hostel_id=None):
    """Passive alert to all assistant wardens about flagged prompt injection."""
    try:
        from sqlalchemy import select
        from models.user import User
        q = select(User).where(
            User.role.in_([UserRole.warden]),
            User.is_active == True,  # noqa: E712
        )
        if hostel_id is not None:
            q = q.where(User.hostel_id == hostel_id)
        wardens = session.execute(q).scalars().all()
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
    1. Fetch complaint
    2. Acknowledge student immediately
    3. Try LLM extraction (category, severity, urgency, affected_count, location, safety_flag, language)
    4. If LLM fails → use keyword fallback classifier
    5. Deterministic routing:
       - interpersonal / critical / safety_flag=True / fallback → approval queue
       - everything else → auto-assign
    6. If injection was flagged → alert warden
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

            # Step 2 — Acknowledge student immediately (before LLM)
            if not complaint.is_anonymous:
                _create_notification_sync(
                    recipient_id=complaint.student_id,
                    title="Complaint Received",
                    body=(
                        f"Your complaint (ID: {complaint_id[:8].upper()}) has been received "
                        "and is being reviewed. You will be notified once it is assigned."
                    ),
                    notification_type=NotificationType.complaint_assigned,
                    session=session,
                )
            session.commit()

            # Step 3 — Try LLM extraction
            llm_result = None
            complaint_text = complaint.sanitized_text or complaint.text

            # If frontend sent a category pre-selection, honour it and skip LLM category extraction
            pre_selected_category = complaint.category

            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    from agents.complaint_classifier import classify_complaint
                    llm_result = loop.run_until_complete(classify_complaint(complaint_text))
                finally:
                    loop.close()
            except Exception as llm_err:
                logger.warning(f"[classify_task] LLM call error: {llm_err}")

            # Step 4 — Build classification from LLM result or fallback
            if llm_result is not None:
                classified_by = ClassifiedBy.llm
                try:
                    category = pre_selected_category or ComplaintCategory(llm_result.category)
                except ValueError:
                    category = ComplaintCategory.uncategorised
                try:
                    severity = ComplaintSeverity(llm_result.severity)
                except ValueError:
                    severity = ComplaintSeverity.medium
                urgency = llm_result.urgency
                affected_count = llm_result.affected_count
                location = llm_result.location
                safety_flag = llm_result.safety_flag
                language_detected = llm_result.language_detected
                logger.info(
                    f"[classify_task] LLM result: category={category.value}, "
                    f"severity={severity.value}, urgency={urgency}, "
                    f"affected={affected_count}, safety={safety_flag}"
                )
            else:
                classified_by = ClassifiedBy.fallback
                fallback = classify_with_fallback(complaint_text)
                category = pre_selected_category or fallback.category
                severity = fallback.severity
                urgency = fallback.urgency
                affected_count = fallback.affected_count
                location = fallback.location
                safety_flag = fallback.safety_flag
                language_detected = fallback.language_detected
                logger.info(
                    f"[classify_task] Fallback result: category={category.value}, severity={severity.value}"
                )

            # Update all extraction fields on complaint
            complaint.category = category
            complaint.severity = severity
            complaint.classified_by = classified_by
            complaint.ai_suggested_category = category
            complaint.urgency = urgency
            complaint.affected_count = affected_count
            complaint.location = location
            complaint.safety_flag = safety_flag
            complaint.language_detected = language_detected

            # Phase 5 — Generate embedding for semantic deduplication (non-blocking)
            try:
                from services.embedding_service import generate_embedding
                loop_emb = asyncio.new_event_loop()
                asyncio.set_event_loop(loop_emb)
                try:
                    emb = loop_emb.run_until_complete(generate_embedding(complaint_text))
                    if emb is not None:
                        complaint.embedding = emb
                        logger.info(f"[classify_task] Embedding generated for {complaint_id}")
                finally:
                    loop_emb.close()
            except Exception as emb_err:
                logger.warning(f"[classify_task] Embedding generation failed (non-critical): {emb_err}")

            session.flush()

            # Step 5 — Deterministic routing (no fake confidence scores)
            # Always send to approval queue if:
            # - category is interpersonal or critical (sensitive, human must review)
            # - safety flag set (health/safety risk detected)
            # - classified by fallback (LLM was unavailable, human should confirm)
            needs_approval = (
                category in (ComplaintCategory.interpersonal, ComplaintCategory.critical)
                or safety_flag is True
                or classified_by == ClassifiedBy.fallback
            )

            if needs_approval:
                warden_id = _get_warden_sync(session, hostel_id=complaint.hostel_id)
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

                from models.approval_queue import ApprovalQueueItem
                queue_item = ApprovalQueueItem(
                    complaint_id=uuid.UUID(complaint_id),
                    ai_suggested_category=category,
                    ai_suggested_severity=severity,
                    ai_suggested_assignee=warden_id,
                    confidence_score=None,
                )
                session.add(queue_item)
                session.flush()

                _transition_complaint_sync(
                    complaint_id, ComplaintStatus.INTAKE, ComplaintStatus.CLASSIFIED,
                    "system", session, note=f"Classified as {category.value}"
                )
                _transition_complaint_sync(
                    complaint_id, ComplaintStatus.CLASSIFIED, ComplaintStatus.AWAITING_APPROVAL,
                    "system", session,
                    note=f"Needs approval: category={category.value}, safety={safety_flag}, by={classified_by.value}"
                )

                _create_notification_sync(
                    recipient_id=warden_id,
                    title="Complaint Needs Review",
                    body=(
                        f"A {category.value} complaint requires your approval. "
                        f"Severity: {severity.value}. "
                        f"{'⚠️ Safety flag raised. ' if safety_flag else ''}"
                        f"Classified by: {classified_by.value}."
                    ),
                    notification_type=NotificationType.approval_needed,
                    session=session,
                )
                logger.info(f"[classify_task] Complaint {complaint_id} → AWAITING_APPROVAL")

            else:
                assignee_id = _find_assignee_sync(category, session, hostel_id=complaint.hostel_id)
                if not assignee_id:
                    assignee_id = _get_warden_sync(session, hostel_id=complaint.hostel_id)
                if not assignee_id:
                    logger.error("[classify_task] No assignee found — no warden exists.")
                    session.commit()
                    return {"status": "error", "reason": "no_assignee_found"}

                complaint.assigned_to = assignee_id
                complaint.requires_approval = False
                session.flush()

                _transition_complaint_sync(
                    complaint_id, ComplaintStatus.INTAKE, ComplaintStatus.CLASSIFIED,
                    "system", session, note=f"Classified as {category.value}"
                )
                _transition_complaint_sync(
                    complaint_id, ComplaintStatus.CLASSIFIED, ComplaintStatus.ASSIGNED,
                    "system", session, note=f"Auto-assigned by {classified_by.value}"
                )

                _create_notification_sync(
                    recipient_id=assignee_id,
                    title="New Complaint Assigned",
                    body=f"A {category.value} complaint has been assigned to you. Severity: {severity.value}.",
                    notification_type=NotificationType.complaint_assigned,
                    session=session,
                )
                logger.info(f"[classify_task] Complaint {complaint_id} → ASSIGNED to {assignee_id}")

            # Step 6 — Flagged injection alert
            if complaint.flagged_input:
                _notify_wardens_flagged_input_sync(complaint_id, session, hostel_id=complaint.hostel_id)

            session.commit()

            # Step 7 — Fire agent task for actionable complaints (async, non-blocking)
            # Triggers when: laundry/maintenance category OR multiple students affected
            # Does NOT fire for complaints going to approval queue (warden handles those)
            agent_eligible = (
                not needs_approval
                and category in (ComplaintCategory.laundry, ComplaintCategory.maintenance)
                or (affected_count is not None and affected_count > 1 and not needs_approval)
            )
            if agent_eligible:
                celery_app.send_task(
                    "tasks.complaint_tasks.run_complaint_agent_task",
                    kwargs=dict(
                        complaint_id=complaint_id,
                        student_id=str(complaint.student_id),
                        hostel_id=str(complaint.hostel_id) if complaint.hostel_id else "",
                        category=category.value,
                        severity=severity.value,
                        affected_count=affected_count or 1,
                        location=location,
                        safety_flag=bool(safety_flag),
                        complaint_text=complaint.sanitized_text or complaint.text,
                    ),
                )
                logger.info(f"[classify_task] Agent task queued for complaint {complaint_id}")

            return {
                "status": "success",
                "complaint_id": complaint_id,
                "classified_by": classified_by.value,
                "category": category.value,
                "severity": severity.value,
                "needs_approval": needs_approval,
                "agent_queued": agent_eligible,
            }

        except Exception as exc:
            session.rollback()
            logger.error(f"[classify_task] Unhandled error for {complaint_id}: {exc}", exc_info=True)
            raise


# ---------------------------------------------------------------------------
# Proactive task: check_stale_complaints
# ---------------------------------------------------------------------------

@celery_app.task(name="tasks.complaint_tasks.check_stale_complaints")
def check_stale_complaints():
    """
    Runs every 2 hours.
    Finds complaints in ASSIGNED or IN_PROGRESS for more than 48 hours
    and escalates them to the warden with a notification.
    """
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select
    from models.complaint import Complaint
    from models.user import User

    STALE_HOURS = 48
    cutoff = datetime.now(timezone.utc) - timedelta(hours=STALE_HOURS)

    logger.info(f"[stale_complaints] Checking for complaints stale > {STALE_HOURS}h")

    with SyncSessionLocal() as session:
        try:
            result = session.execute(
                select(Complaint).where(
                    Complaint.status.in_([ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS]),
                    Complaint.updated_at < cutoff,
                )
            )
            stale = result.scalars().all()

            if not stale:
                logger.info("[stale_complaints] No stale complaints found")
                return {"status": "ok", "escalated": 0}

            escalated = 0
            for complaint in stale:
                try:
                    warden_id = _get_warden_sync(session, hostel_id=complaint.hostel_id)
                    if not warden_id:
                        continue

                    _transition_complaint_sync(
                        complaint_id=str(complaint.id),
                        from_state=complaint.status,
                        to_state=ComplaintStatus.ESCALATED,
                        triggered_by="system:stale",
                        session=session,
                        note=f"Auto-escalated — unresolved for >{STALE_HOURS}h",
                    )
                    _create_notification_sync(
                        recipient_id=warden_id,
                        title="Stale Complaint Escalated",
                        body=(
                            f"Complaint {str(complaint.id)[:8].upper()} has been "
                            f"unresolved for over {STALE_HOURS} hours and has been escalated."
                        ),
                        notification_type=NotificationType.complaint_escalated,
                        session=session,
                    )
                    escalated += 1
                    logger.info(f"[stale_complaints] Escalated complaint {complaint.id}")
                except Exception as e:
                    logger.error(f"[stale_complaints] Failed for {complaint.id}: {e}")
                    session.rollback()
                    continue

            session.commit()
            logger.info(f"[stale_complaints] Done — {escalated} escalated")
            return {"status": "ok", "escalated": escalated}

        except Exception as exc:
            session.rollback()
            logger.error(f"[stale_complaints] Unhandled error: {exc}", exc_info=True)
            raise


# ---------------------------------------------------------------------------
# Agent task — fires after classification for laundry/maintenance/multi-person
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=5,
    name="tasks.complaint_tasks.run_complaint_agent_task",
)
def run_complaint_agent_task(
    self,
    complaint_id: str,
    student_id: str,
    hostel_id: str,
    category: str,
    severity: str,
    affected_count: int,
    location: str | None,
    safety_flag: bool,
    complaint_text: str,
):
    """
    Runs the Groq tool-calling agent for a complaint that has been classified
    and routed. Operates on a fresh async DB session — does not share the
    classification task's session.

    Eligible complaints: laundry, maintenance, or affected_count > 1
    (and not sent to the approval queue, which wardens handle directly).
    """
    from database import AsyncSessionLocal
    from agents.complaint_agent import run_complaint_agent

    logger.info(f"[agent_task] Starting agent for complaint {complaint_id}")

    async def _run():
        async with AsyncSessionLocal() as db:
            return await run_complaint_agent(
                complaint_id=complaint_id,
                student_id=student_id,
                hostel_id=hostel_id,
                category=category,
                severity=severity,
                affected_count=affected_count,
                location=location,
                safety_flag=safety_flag,
                complaint_text=complaint_text,
                db=db,
            )

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_run())
        finally:
            loop.close()
        logger.info(f"[agent_task] Agent completed for {complaint_id}: {result.get('status')}")
        return result
    except Exception as exc:
        logger.error(f"[agent_task] Unhandled error for {complaint_id}: {exc}", exc_info=True)
        raise
