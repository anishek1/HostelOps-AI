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
from schemas.metrics import (
    ComplaintsAnalytics,
    DashboardMetrics,
    LaundryAnalytics,
    MessAnalytics,
)

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
# Sprint 6: Pending counts and Analytics
# ---------------------------------------------------------------------------

async def get_pending_registrations_count(db: AsyncSession) -> int:
    """Non-verified, non-rejected student accounts."""
    result = await db.execute(
        select(func.count(User.id))
        .where(User.role == "student")
        .where(User.is_verified == False)
        .where(User.is_rejected == False)
    )
    return result.scalar() or 0


async def get_pending_approval_queue_count(db: AsyncSession) -> int:
    """Pending items in approval queue."""
    result = await db.execute(
        select(func.count(ApprovalQueueItem.id))
        .where(ApprovalQueueItem.status == "pending")
    )
    return result.scalar() or 0


async def get_complaints_analytics(
    days: int, category: str | None, status: str | None, db: AsyncSession
) -> ComplaintsAnalytics:
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    base_query = select(Complaint).where(Complaint.created_at >= cutoff)
    if category:
        base_query = base_query.where(Complaint.category == category)
    if status:
        base_query = base_query.where(Complaint.status == status)

    result = await db.execute(base_query)
    complaints = result.scalars().all()

    by_category = {}
    by_status = {}
    by_severity = {}
    total_hours = 0.0
    resolved_count = 0
    llm_count = 0
    fallback_count = 0

    for c in complaints:
        # Categorization
        if c.category is not None:
            by_category[c.category.value] = by_category.get(c.category.value, 0) + 1
        by_status[c.status.value] = by_status.get(c.status.value, 0) + 1
        
        # Severity
        sev = c.severity.value if c.severity else "unassigned"
        by_severity[sev] = by_severity.get(sev, 0) + 1
        
        # Classification source
        if c.classified_by and c.classified_by.value == "llm":
            llm_count += 1
        elif c.classified_by and c.classified_by.value == "fallback":
            fallback_count += 1

        # Resolution time
        if c.status == ComplaintStatus.RESOLVED and c.resolved_at:
            hours = (c.resolved_at - c.created_at).total_seconds() / 3600
            total_hours += hours
            resolved_count += 1

    avg_resolution = round(total_hours / resolved_count, 2) if resolved_count > 0 else 0.0

    return ComplaintsAnalytics(
        period_days=days,
        total_complaints=len(complaints),
        by_category=by_category,
        by_status=by_status,
        by_severity=by_severity,
        avg_resolution_hours=avg_resolution,
        classified_by_llm=llm_count,
        classified_by_fallback=fallback_count,
        computed_at=datetime.utcnow()
    )


async def get_mess_analytics(days: int, db: AsyncSession) -> MessAnalytics:
    from datetime import date, timedelta as td
    cutoff = date.today() - td(days=days)

    result = await db.execute(
        select(MessFeedback).where(MessFeedback.date >= cutoff)
    )
    feedback_list = result.scalars().all()

    daily_counts = {}
    total_scores = {
        "food_quality": 0,
        "hygiene": 0,
        "menu_variety": 0,
        "food_quantity": 0,
        "timing": 0,
    }

    # Handle alerting
    # We define an "alert" if any score is < 2
    alerts = 0

    for f in feedback_list:
        date_str = f.date.isoformat()
        daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
        total_scores["food_quality"] += f.food_quality
        total_scores["hygiene"] += f.hygiene
        total_scores["menu_variety"] += f.menu_variety
        total_scores["food_quantity"] += f.food_quantity
        total_scores["timing"] += f.timing

        if f.food_quality < 2 or f.hygiene < 2 or f.menu_variety < 2:
            alerts += 1

    total = len(feedback_list)
    num_dims = 5
    avg_by_dim = {
        "food_quality": round(total_scores["food_quality"] / total, 2) if total else 0.0,
        "hygiene": round(total_scores["hygiene"] / total, 2) if total else 0.0,
        "menu_variety": round(total_scores["menu_variety"] / total, 2) if total else 0.0,
        "food_quantity": round(total_scores["food_quantity"] / total, 2) if total else 0.0,
        "timing": round(total_scores["timing"] / total, 2) if total else 0.0,
    }

    overall = sum(avg_by_dim.values()) / num_dims if total else 0.0

    return MessAnalytics(
        period_days=days,
        total_feedback=total,
        daily_participation=daily_counts,
        avg_by_dimension=avg_by_dim,
        overall_avg=round(overall, 2),
        alerts_this_period=alerts,
        computed_at=datetime.utcnow()
    )


async def get_laundry_analytics(days: int, db: AsyncSession) -> LaundryAnalytics:
    from datetime import date, timedelta as td
    cutoff = date.today() - td(days=days)

    result = await db.execute(
        select(LaundrySlot)
        .where(LaundrySlot.slot_date >= cutoff)
        .where(LaundrySlot.booked_at.isnot(None))
    )
    slots = result.scalars().all()

    total_bookings = len(slots)
    cancellations = sum(1 for s in slots if s.booking_status == LaundrySlotStatus.cancelled)
    noshows = sum(1 for s in slots if s.booking_status == LaundrySlotStatus.no_show)

    cancel_rate = round(cancellations / total_bookings, 4) if total_bookings else 0.0
    noshow_rate = round(noshows / total_bookings, 4) if total_bookings else 0.0

    return LaundryAnalytics(
        period_days=days,
        total_bookings=total_bookings,
        total_cancellations=cancellations,
        total_noshows=noshows,
        noshow_rate=noshow_rate,
        cancellation_rate=cancel_rate,
        computed_at=datetime.utcnow()
    )


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
    
    pending_reg = await get_pending_registrations_count(db)
    pending_appr = await get_pending_approval_queue_count(db)

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
        pending_registrations=pending_reg,
        pending_approval_queue=pending_appr,
        drift_alert=drift_alert,
        computed_at=datetime.utcnow(),
    )
