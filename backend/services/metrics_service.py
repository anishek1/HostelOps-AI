"""
services/metrics_service.py — HostelOps AI
============================================
Analytics and evaluation metrics service.
Computes PRD Section 6.2 metrics: misclassification rate, override rate by category,
false high-severity rate, resolution confirmation rate, approval queue latency,
mess participation rate, and laundry no-show rate.
Sprint 5: New service.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.approval_queue import ApprovalQueueItem
from models.complaint import Complaint
from models.laundry_slot import LaundrySlot
from models.mess_feedback import MessFeedback
from models.override_log import OverrideLog
from models.user import User
from schemas.enums import ComplaintStatus, LaundrySlotStatus
from schemas.metrics import DashboardMetrics

logger = logging.getLogger(__name__)

_COMPLAINT_CATEGORIES = ["mess", "laundry", "maintenance", "interpersonal", "critical", "uncategorised"]


# ---------------------------------------------------------------------------
# Individual metric helpers
# ---------------------------------------------------------------------------

async def get_misclassification_rate(days: int, db: AsyncSession) -> float:
    """Overrides / total AI-classified complaints in rolling window."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    total_result = await db.execute(
        select(func.count(Complaint.id))
        .where(Complaint.created_at >= cutoff)
        .where(Complaint.classified_by == "llm")
    )
    total = total_result.scalar() or 0
    if total == 0:
        return 0.0

    override_result = await db.execute(
        select(func.count(OverrideLog.id))
        .where(OverrideLog.created_at >= cutoff)
    )
    overrides = override_result.scalar() or 0

    rate = overrides / total
    logger.debug(f"Misclassification rate: {overrides}/{total} = {rate:.3f}")
    return round(rate, 4)


async def get_override_rate_by_category(days: int, db: AsyncSession) -> Dict[str, float]:
    """Per-category override rate."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = {}

    for cat in _COMPLAINT_CATEGORIES:
        total_res = await db.execute(
            select(func.count(Complaint.id))
            .where(Complaint.created_at >= cutoff)
            .where(Complaint.category == cat)
            .where(Complaint.classified_by == "llm")
        )
        total = total_res.scalar() or 0
        if total == 0:
            result[cat] = 0.0
            continue

        override_res = await db.execute(
            select(func.count(OverrideLog.id))
            .join(Complaint, OverrideLog.complaint_id == Complaint.id)
            .where(OverrideLog.created_at >= cutoff)
            .where(Complaint.category == cat)
        )
        overrides = override_res.scalar() or 0
        result[cat] = round(overrides / total, 4)

    return result


async def get_false_high_severity_rate(days: int, db: AsyncSession) -> float:
    """AI-classified high-severity complaints later downgraded by warden."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    total_res = await db.execute(
        select(func.count(Complaint.id))
        .where(Complaint.created_at >= cutoff)
        .where(Complaint.severity == "high")
        .where(Complaint.classified_by == "llm")
    )
    total = total_res.scalar() or 0
    if total == 0:
        return 0.0

    # Overrides where original severity was high — any override counts as downgrade
    downgrade_res = await db.execute(
        select(func.count(OverrideLog.id))
        .join(Complaint, OverrideLog.complaint_id == Complaint.id)
        .where(OverrideLog.created_at >= cutoff)
        .where(Complaint.severity == "high")
    )
    downgrades = downgrade_res.scalar() or 0
    return round(downgrades / total, 4)


async def get_resolution_confirmation_rate(days: int, db: AsyncSession) -> float:
    """Student-confirmed resolutions / total resolved complaints."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    total_res = await db.execute(
        select(func.count(Complaint.id))
        .where(Complaint.updated_at >= cutoff)
        .where(Complaint.status == ComplaintStatus.RESOLVED)
    )
    total = total_res.scalar() or 0
    if total == 0:
        return 0.0

    confirmed_res = await db.execute(
        select(func.count(Complaint.id))
        .where(Complaint.updated_at >= cutoff)
        .where(Complaint.status == ComplaintStatus.RESOLVED)
        .where(Complaint.resolved_confirmed_at.isnot(None))
    )
    confirmed = confirmed_res.scalar() or 0
    return round(confirmed / total, 4)


async def get_avg_approval_queue_latency(days: int, db: AsyncSession) -> float:
    """Average minutes from queue item creation to review."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            func.avg(
                func.extract(
                    "epoch",
                    ApprovalQueueItem.reviewed_at - ApprovalQueueItem.created_at
                ) / 60
            )
        )
        .where(ApprovalQueueItem.created_at >= cutoff)
        .where(ApprovalQueueItem.reviewed_at.isnot(None))
    )
    avg = result.scalar()
    return round(float(avg), 2) if avg else 0.0


async def get_mess_participation_rate(db: AsyncSession) -> float:
    """Today's unique feedback submitters / total active students."""
    from datetime import date
    today = date.today()

    total_res = await db.execute(
        select(func.count(User.id)).where(User.role == "student").where(User.is_active == True)  # noqa: E712
    )
    total_students = total_res.scalar() or 1

    participants_res = await db.execute(
        select(func.count(func.distinct(MessFeedback.student_id)))
        .where(MessFeedback.date == today)
    )
    participants = participants_res.scalar() or 0
    return round(participants / total_students, 4)


async def get_laundry_noshow_rate(days: int, db: AsyncSession) -> float:
    """No-show slots / total booked slots in the period."""
    from datetime import date, timedelta as td
    cutoff = date.today() - td(days=days)

    total_res = await db.execute(
        select(func.count(LaundrySlot.id))
        .where(LaundrySlot.booked_at.isnot(None))
        .where(LaundrySlot.slot_date >= cutoff)
    )
    total = total_res.scalar() or 1

    noshow_res = await db.execute(
        select(func.count(LaundrySlot.id))
        .where(LaundrySlot.booking_status == LaundrySlotStatus.no_show)
        .where(LaundrySlot.slot_date >= cutoff)
    )
    noshows = noshow_res.scalar() or 0
    return round(noshows / total, 4)


# ---------------------------------------------------------------------------
# Aggregated dashboard
# ---------------------------------------------------------------------------

async def get_full_dashboard_metrics(days: int, db: AsyncSession) -> DashboardMetrics:
    """Compute all evaluation metrics and return a DashboardMetrics object."""
    logger.info(f"Computing dashboard metrics for last {days} days")

    misclassification = await get_misclassification_rate(days, db)
    override_by_cat = await get_override_rate_by_category(days, db)
    false_high = await get_false_high_severity_rate(days, db)
    confirmation = await get_resolution_confirmation_rate(days, db)
    latency = await get_avg_approval_queue_latency(days, db)
    mess_participation = await get_mess_participation_rate(db)
    laundry_noshow = await get_laundry_noshow_rate(days, db)

    drift_alert = misclassification > 0.25
    if drift_alert:
        logger.warning(f"DRIFT ALERT: misclassification rate {misclassification:.1%} exceeds 25% threshold")

    return DashboardMetrics(
        period_days=days,
        misclassification_rate=misclassification,
        override_rate_by_category=override_by_cat,
        false_high_severity_rate=false_high,
        resolution_confirmation_rate=confirmation,
        avg_approval_queue_latency_minutes=latency,
        mess_participation_rate=mess_participation,
        laundry_noshow_rate=laundry_noshow,
        drift_alert=drift_alert,
        computed_at=datetime.utcnow(),
    )
