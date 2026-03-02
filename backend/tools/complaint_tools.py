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
