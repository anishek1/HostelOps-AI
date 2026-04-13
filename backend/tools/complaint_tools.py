"""
complaint_tools.py — HostelOps AI
===================================
Agent 1 typed tool definitions.
Each tool has a strict Pydantic input schema and typed output.
Tools call services — they never access the DB directly.
All tools are async.
"""
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.enums import ComplaintCategory, ComplaintSeverity, NotificationType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------

class AssignComplaintInput(BaseModel):
    complaint_id: str
    assignee_id: str
    severity: ComplaintSeverity
    category: ComplaintCategory


class EscalateComplaintInput(BaseModel):
    complaint_id: str
    escalation_target: str  # user_id of the target warden
    reason: str


class RequestHumanApprovalInput(BaseModel):
    complaint_id: str
    ai_category: ComplaintCategory
    ai_severity: ComplaintSeverity
    ai_assignee_id: str
    confidence: float


class AcknowledgeStudentInput(BaseModel):
    complaint_id: str
    student_id: str
    is_anonymous: bool


class RouteToAgentInput(BaseModel):
    complaint_id: str
    target_agent: str  # "laundry" | "mess" | "maintenance"
    complaint_text: str
    category: ComplaintCategory


class LogOverrideInput(BaseModel):
    complaint_id: str
    warden_id: str
    original: dict[str, Any]
    corrected: dict[str, Any]
    reason: str


# ---------------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------------

class AssignmentResult(BaseModel):
    success: bool
    notified: bool
    assigned_at: datetime


class EscalationResult(BaseModel):
    success: bool
    queue_item_id: str | None


class ApprovalRequest(BaseModel):
    queue_item_id: str
    created_at: datetime


class AcknowledgementResult(BaseModel):
    success: bool
    message: str


class RoutingResult(BaseModel):
    success: bool
    agent_received: str


class LogResult(BaseModel):
    log_id: str


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

async def assign_complaint_tool(
    input_data: AssignComplaintInput,
    db: AsyncSession,
) -> AssignmentResult:
    """
    Assigns a complaint to a staff member.
    Calls complaint_service.assign_complaint().
    """
    import uuid
    from services.complaint_service import assign_complaint
    from services.notification_service import notify_user

    complaint = await assign_complaint(
        complaint_id=input_data.complaint_id,
        assignee_id=input_data.assignee_id,
        category=input_data.category,
        severity=input_data.severity,
        classified_by="llm",
        db=db,
    )

    # Notify the assigned staff member
    notified = False
    try:
        await notify_user(
            recipient_id=uuid.UUID(input_data.assignee_id),
            title="Complaint Assigned",
            body=f"A new {input_data.category.value} complaint has been assigned to you.",
            notification_type=NotificationType.complaint_assigned,
            db=db,
        )
        notified = True
    except Exception as e:
        logger.warning(f"Notification failed for assignee {input_data.assignee_id}: {e}")

    return AssignmentResult(
        success=True,
        notified=notified,
        assigned_at=complaint.updated_at,
    )


async def escalate_complaint_tool(
    input_data: EscalateComplaintInput,
    db: AsyncSession,
) -> EscalationResult:
    """
    Escalates a complaint to a senior warden.
    Transitions complaint → ESCALATED and notifies the target.
    """
    import uuid
    from services.complaint_service import transition_complaint, get_complaint
    from services.notification_service import notify_user
    from schemas.enums import ComplaintStatus, UserRole
    from sqlalchemy import select
    from models.user import User

    complaint = await get_complaint(
        complaint_id=input_data.complaint_id,
        requesting_user_id=input_data.escalation_target,
        requesting_user_role=UserRole.warden,
        db=db,
    )
    await transition_complaint(
        complaint_id=input_data.complaint_id,
        from_state=complaint.status,
        to_state=ComplaintStatus.ESCALATED,
        triggered_by="system",
        db=db,
        note=input_data.reason,
    )
    try:
        await notify_user(
            recipient_id=uuid.UUID(input_data.escalation_target),
            title="Complaint Escalated",
            body=f"Complaint escalated: {input_data.reason}",
            notification_type=NotificationType.approval_needed,
            db=db,
        )
    except Exception as e:
        logger.warning(f"Escalation notification failed: {e}")

    return EscalationResult(success=True, queue_item_id=None)


async def request_human_approval_tool(
    input_data: RequestHumanApprovalInput,
    db: AsyncSession,
) -> ApprovalRequest:
    """
    Routes a complaint to the Warden approval queue.
    Creates an ApprovalQueueItem and transitions → AWAITING_APPROVAL.
    """
    from services.complaint_service import send_to_approval_queue

    queue_item = await send_to_approval_queue(
        complaint_id=input_data.complaint_id,
        ai_category=input_data.ai_category,
        ai_severity=input_data.ai_severity,
        ai_assignee_id=input_data.ai_assignee_id,
        confidence=input_data.confidence,
        db=db,
    )
    return ApprovalRequest(
        queue_item_id=str(queue_item.id),
        created_at=queue_item.created_at,
    )


async def acknowledge_student_tool(
    input_data: AcknowledgeStudentInput,
    db: AsyncSession,
) -> AcknowledgementResult:
    """
    Sends an acknowledgement notification to the student.
    ALWAYS succeeds — never raises. Catches all exceptions internally.
    Called immediately when a complaint is received, before any LLM work.
    """
    import uuid
    from services.notification_service import notify_user

    try:
        if not input_data.is_anonymous:
            await notify_user(
                recipient_id=uuid.UUID(input_data.student_id),
                title="Complaint Received",
                body=(
                    f"Your complaint (ID: {input_data.complaint_id[:8]}...) has been received "
                    "and is being reviewed. You will be notified once it is assigned."
                ),
                notification_type=NotificationType.complaint_assigned,
                db=db,
            )
        return AcknowledgementResult(
            success=True,
            message="Acknowledgement sent successfully.",
        )
    except Exception as e:
        logger.error(f"[acknowledge_student_tool] Failed to send acknowledgement: {e}")
        return AcknowledgementResult(
            success=False,
            message=f"Acknowledgement failed (non-critical): {e}",
        )


async def route_to_agent_tool(
    input_data: RouteToAgentInput,
    db: AsyncSession,
) -> RoutingResult:
    """
    Routes a classified complaint to the appropriate specialist agent.
    In Sprint 2 this logs the routing intent — actual agent hand-off in Sprint 3+.
    """
    logger.info(
        f"[route_to_agent_tool] Routing complaint {input_data.complaint_id} "
        f"to agent '{input_data.target_agent}' (category: {input_data.category.value})"
    )
    return RoutingResult(success=True, agent_received=input_data.target_agent)


async def log_override_tool(
    input_data: LogOverrideInput,
    db: AsyncSession,
) -> LogResult:
    """
    Logs a warden override (manual correction of AI classification).
    Creates an OverrideLog record in the database via override_log_service.
    """
    from services.override_log_service import create_override_log
    from schemas.enums import ComplaintCategory, ComplaintSeverity, OverrideReason

    log = await create_override_log(
        complaint_id=input_data.complaint_id,
        warden_id=input_data.warden_id,
        original_category=ComplaintCategory(
            input_data.original.get("category", ComplaintCategory.uncategorised.value)
        ),
        corrected_category=ComplaintCategory(
            input_data.corrected.get("category", ComplaintCategory.uncategorised.value)
        ),
        original_severity=ComplaintSeverity(
            input_data.original.get("severity", ComplaintSeverity.medium.value)
        ),
        corrected_severity=ComplaintSeverity(
            input_data.corrected.get("severity", ComplaintSeverity.medium.value)
        ),
        original_assignee=input_data.original.get("assignee_id"),
        corrected_assignee=input_data.corrected.get("assignee_id"),
        reason=OverrideReason.other,
        db=db,
    )
    return LogResult(log_id=str(log.id))


# ---------------------------------------------------------------------------
# Agent tools — used by complaint_agent.py (Groq function calling)
# ---------------------------------------------------------------------------

class GetComplaintHistoryInput(BaseModel):
    student_id: str
    hostel_id: str
    limit: int = 5


class ComplaintHistoryResult(BaseModel):
    complaints: list[dict]
    total: int


class FindSimilarInput(BaseModel):
    hostel_id: str
    category: ComplaintCategory
    location: str | None = None
    complaint_text: str | None = None  # if provided, uses vector similarity
    complaint_id: str | None = None    # exclude self from results
    limit: int = 5


class SimilarComplaintsResult(BaseModel):
    complaints: list[dict]
    total: int


class GetStaffInput(BaseModel):
    role: str  # "laundry_man" | "mess_staff" | "warden"
    hostel_id: str


class StaffAvailabilityResult(BaseModel):
    staff: list[dict]
    count: int


class CheckMachineInput(BaseModel):
    machine_id: str
    hostel_id: str


class MachineStatusResult(BaseModel):
    machine_id: str
    name: str
    status: str
    floor: str | None
    is_active: bool
    found: bool


class EscalateInput(BaseModel):
    complaint_id: str
    reason: str
    hostel_id: str


class EscalateResult(BaseModel):
    success: bool
    new_status: str


class RescheduleInput(BaseModel):
    machine_id: str
    hostel_id: str


class RescheduleResult(BaseModel):
    slots_cancelled: int
    students_notified: int


class NotifyStudentInput(BaseModel):
    student_id: str
    title: str
    body: str
    notification_type: str = "complaint_assigned"


class NotifyResult(BaseModel):
    success: bool


async def get_student_complaint_history(
    input_data: GetComplaintHistoryInput,
    db: AsyncSession,
) -> ComplaintHistoryResult:
    """Returns recent complaints filed by this student in this hostel."""
    import uuid as _uuid
    from sqlalchemy import select
    from models.complaint import Complaint

    result = await db.execute(
        select(Complaint)
        .where(
            Complaint.student_id == _uuid.UUID(input_data.student_id),
            Complaint.hostel_id == _uuid.UUID(input_data.hostel_id),
        )
        .order_by(Complaint.created_at.desc())
        .limit(input_data.limit)
    )
    rows = result.scalars().all()
    complaints = [
        {
            "id": str(c.id),
            "category": c.category.value if c.category else None,
            "severity": c.severity.value if c.severity else None,
            "status": c.status.value,
            "created_at": c.created_at.isoformat(),
        }
        for c in rows
    ]
    return ComplaintHistoryResult(complaints=complaints, total=len(complaints))


async def find_similar_open_complaints(
    input_data: FindSimilarInput,
    db: AsyncSession,
) -> SimilarComplaintsResult:
    """
    Finds open complaints similar to the given one.
    Uses pgvector cosine similarity if complaint_text is provided and embeddings are enabled.
    Falls back to category+location matching otherwise.
    """
    # Try vector similarity first
    if input_data.complaint_text:
        try:
            from services.embedding_service import generate_embedding, find_similar_by_vector
            emb = await generate_embedding(input_data.complaint_text)
            if emb is not None:
                similar = await find_similar_by_vector(
                    embedding=emb,
                    hostel_id=input_data.hostel_id,
                    exclude_id=input_data.complaint_id,
                    limit=input_data.limit,
                    db=db,
                )
                return SimilarComplaintsResult(complaints=similar, total=len(similar))
        except Exception as e:
            logger.warning(f"[find_similar] Vector search failed, falling back: {e}")

    # Fallback: category + location matching
    import uuid as _uuid
    from sqlalchemy import select
    from models.complaint import Complaint
    from schemas.enums import ComplaintStatus

    open_statuses = [
        ComplaintStatus.INTAKE,
        ComplaintStatus.CLASSIFIED,
        ComplaintStatus.AWAITING_APPROVAL,
        ComplaintStatus.ASSIGNED,
        ComplaintStatus.IN_PROGRESS,
    ]
    q = (
        select(Complaint)
        .where(
            Complaint.hostel_id == _uuid.UUID(input_data.hostel_id),
            Complaint.category == input_data.category,
            Complaint.status.in_(open_statuses),
        )
        .order_by(Complaint.created_at.desc())
        .limit(input_data.limit)
    )
    result = await db.execute(q)
    rows = result.scalars().all()

    if input_data.location:
        loc = input_data.location.lower()
        rows = [r for r in rows if r.location and loc in r.location.lower()]

    complaints = [
        {
            "id": str(c.id),
            "status": c.status.value,
            "location": c.location,
            "affected_count": c.affected_count,
            "created_at": c.created_at.isoformat(),
        }
        for c in rows
    ]
    return SimilarComplaintsResult(complaints=complaints, total=len(complaints))


async def get_staff_availability(
    input_data: GetStaffInput,
    db: AsyncSession,
) -> StaffAvailabilityResult:
    """Returns active staff members with the given role in the hostel."""
    import uuid as _uuid
    from sqlalchemy import select
    from models.user import User
    from schemas.enums import UserRole

    try:
        role = UserRole(input_data.role)
    except ValueError:
        role = UserRole.warden

    result = await db.execute(
        select(User).where(
            User.role == role,
            User.is_active == True,  # noqa: E712
            User.hostel_id == _uuid.UUID(input_data.hostel_id),
        )
    )
    users = result.scalars().all()
    staff = [{"id": str(u.id), "name": u.name, "role": u.role.value} for u in users]
    return StaffAvailabilityResult(staff=staff, count=len(staff))


async def check_machine_status(
    input_data: CheckMachineInput,
    db: AsyncSession,
) -> MachineStatusResult:
    """Returns the current status of a laundry machine."""
    import uuid as _uuid
    from sqlalchemy import select
    from models.machine import Machine

    result = await db.execute(
        select(Machine).where(
            Machine.id == _uuid.UUID(input_data.machine_id),
            Machine.hostel_id == _uuid.UUID(input_data.hostel_id),
        )
    )
    machine = result.scalar_one_or_none()
    if not machine:
        return MachineStatusResult(
            machine_id=input_data.machine_id,
            name="unknown",
            status="not_found",
            floor=None,
            is_active=False,
            found=False,
        )
    return MachineStatusResult(
        machine_id=str(machine.id),
        name=machine.name,
        status=machine.status.value,
        floor=machine.floor,
        is_active=machine.is_active,
        found=True,
    )


async def escalate_complaint_agent(
    input_data: EscalateInput,
    db: AsyncSession,
) -> EscalateResult:
    """
    Escalates a complaint directly to the warden for urgent review.
    Finds the warden for this hostel and transitions complaint → ESCALATED.
    """
    import uuid as _uuid
    from sqlalchemy import select
    from models.complaint import Complaint
    from models.user import User
    from services.complaint_service import transition_complaint
    from services.notification_service import notify_user
    from schemas.enums import ComplaintStatus, UserRole

    result = await db.execute(
        select(Complaint).where(Complaint.id == _uuid.UUID(input_data.complaint_id))
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        return EscalateResult(success=False, new_status="not_found")

    # Find warden for this hostel
    warden_result = await db.execute(
        select(User).where(
            User.role == UserRole.warden,
            User.is_active == True,  # noqa: E712
            User.hostel_id == _uuid.UUID(input_data.hostel_id),
        )
    )
    warden = warden_result.scalars().first()

    escalatable = [
        ComplaintStatus.INTAKE,
        ComplaintStatus.CLASSIFIED,
        ComplaintStatus.AWAITING_APPROVAL,
        ComplaintStatus.ASSIGNED,
        ComplaintStatus.IN_PROGRESS,
    ]
    if complaint.status not in escalatable:
        return EscalateResult(success=False, new_status=complaint.status.value)

    await transition_complaint(
        complaint_id=input_data.complaint_id,
        from_state=complaint.status,
        to_state=ComplaintStatus.ESCALATED,
        triggered_by="system",
        db=db,
        note=f"Agent escalation: {input_data.reason}",
    )

    if warden:
        try:
            await notify_user(
                recipient_id=warden.id,
                title="Complaint Escalated by Agent",
                body=f"Complaint {input_data.complaint_id[:8].upper()} escalated: {input_data.reason}",
                notification_type=NotificationType.approval_needed,
                db=db,
            )
        except Exception as e:
            logger.warning(f"Escalation warden notify failed: {e}")

    return EscalateResult(success=True, new_status=ComplaintStatus.ESCALATED.value)


async def reschedule_affected_slots(
    input_data: RescheduleInput,
    db: AsyncSession,
) -> RescheduleResult:
    """
    Cancels upcoming booked slots for a broken machine and notifies affected students.
    """
    import uuid as _uuid
    from datetime import date
    from sqlalchemy import select
    from models.laundry_slot import LaundrySlot
    from schemas.enums import LaundrySlotStatus

    result = await db.execute(
        select(LaundrySlot).where(
            LaundrySlot.machine_id == _uuid.UUID(input_data.machine_id),
            LaundrySlot.hostel_id == _uuid.UUID(input_data.hostel_id),
            LaundrySlot.booking_status == LaundrySlotStatus.booked,
            LaundrySlot.slot_date >= date.today(),
        )
    )
    slots = result.scalars().all()

    notified = 0
    for slot in slots:
        slot.booking_status = LaundrySlotStatus.cancelled
        db.add(slot)
        if slot.student_id:
            try:
                from services.notification_service import notify_user
                await notify_user(
                    recipient_id=slot.student_id,
                    title="Laundry Slot Cancelled",
                    body=(
                        f"Your laundry slot on {slot.slot_date} at {slot.slot_time} "
                        "has been cancelled because the machine is under repair. "
                        "Please rebook when the machine is back online."
                    ),
                    notification_type=NotificationType.laundry_reminder,
                    db=db,
                )
                notified += 1
            except Exception as e:
                logger.warning(f"reschedule notify failed for slot {slot.id}: {e}")

    await db.flush()
    return RescheduleResult(slots_cancelled=len(slots), students_notified=notified)


async def notify_student_tool(
    input_data: NotifyStudentInput,
    db: AsyncSession,
) -> NotifyResult:
    """Sends a direct notification to a student."""
    import uuid as _uuid
    from services.notification_service import notify_user

    try:
        ntype = NotificationType(input_data.notification_type)
    except ValueError:
        ntype = NotificationType.complaint_assigned

    try:
        await notify_user(
            recipient_id=_uuid.UUID(input_data.student_id),
            title=input_data.title,
            body=input_data.body,
            notification_type=ntype,
            db=db,
        )
        return NotifyResult(success=True)
    except Exception as e:
        logger.error(f"[notify_student_tool] Failed: {e}")
        return NotifyResult(success=False)
