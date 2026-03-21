"""
services/mess_service.py — HostelOps AI
==========================================
Agent 3 business logic — feedback submission, alerting, trend analysis.
The existing MessFeedback model stores 5 dimension scores: food_quality,
food_quantity, hygiene, menu_variety, timing. Overall rating = avg of 5.
Golden Rule 4: No business logic in routes.
Golden Rule 16: Always call await db.refresh(obj) after await db.commit().
"""
import logging
import uuid
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.mess_alert import MessAlert
from models.mess_feedback import MessFeedback
from models.user import User
from schemas.enums import AlertType, MealPeriod, MessDimension, NotificationType, UserRole
from schemas.mess import MessSummaryResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feedback Submission
# ---------------------------------------------------------------------------

async def submit_feedback(
    student_id: uuid.UUID,
    meal: MealPeriod,
    feedback_date: date,
    food_quality: int,
    food_quantity: int,
    hygiene: int,
    menu_variety: int,
    timing: int,
    comment: Optional[str],
    db: AsyncSession,
    hostel_id=None,
) -> MessFeedback:
    """
    Saves 5-dimension feedback. One submission per student per meal per date.
    Sprint 7b: Updates feedback_streak on the student's User record.
    Raises ValueError if duplicate detected.
    """
    existing = await db.execute(
        select(MessFeedback)
        .where(MessFeedback.student_id == student_id)
        .where(MessFeedback.meal == meal)
        .where(MessFeedback.date == feedback_date)
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"Feedback already submitted for {meal.value} on {feedback_date}")

    feedback = MessFeedback(
        student_id=student_id,
        meal=meal,
        date=feedback_date,
        food_quality=food_quality,
        food_quantity=food_quantity,
        hygiene=hygiene,
        menu_variety=menu_variety,
        timing=timing,
        comment=comment,
        hostel_id=hostel_id,
    )
    db.add(feedback)

    # Sprint 7b: Update feedback streak on the student record
    student = await db.get(User, student_id)
    if student:
        today = date.today()
        yesterday = today - timedelta(days=1)
        if student.last_feedback_date == yesterday:
            student.feedback_streak = (student.feedback_streak or 0) + 1
        else:
            student.feedback_streak = 1
        student.last_feedback_date = today
        db.add(student)

    await db.commit()
    await db.refresh(feedback)
    logger.info(f"Feedback submitted by {student_id} for {meal.value} on {feedback_date}")
    return feedback


# ---------------------------------------------------------------------------
# Summary and Trend
# ---------------------------------------------------------------------------

async def get_daily_summary(
    feedback_date: date,
    meal: Optional[MealPeriod],
    db: AsyncSession,
    hostel_id=None,
) -> MessSummaryResponse:
    """Computes average scores across all 5 dimensions for a date and optional meal."""
    query = select(MessFeedback).where(MessFeedback.date == feedback_date)
    if meal:
        query = query.where(MessFeedback.meal == meal)
    if hostel_id is not None:
        query = query.where(MessFeedback.hostel_id == hostel_id)

    result = await db.execute(query)
    feedbacks = result.scalars().all()

    if not feedbacks:
        return MessSummaryResponse(
            feedback_date=feedback_date,
            meal=meal,
            avg_food_quality=0.0,
            avg_food_quantity=0.0,
            avg_hygiene=0.0,
            avg_menu_variety=0.0,
            avg_timing=0.0,
            overall_avg=0.0,
            participation_count=0,
            trend="stable",
        )

    n = len(feedbacks)
    avg_fq = sum(f.food_quality for f in feedbacks) / n
    avg_qty = sum(f.food_quantity for f in feedbacks) / n
    avg_hyg = sum(f.hygiene for f in feedbacks) / n
    avg_mv = sum(f.menu_variety for f in feedbacks) / n
    avg_tim = sum(f.timing for f in feedbacks) / n
    overall = (avg_fq + avg_qty + avg_hyg + avg_mv + avg_tim) / 5

    # Trend: compare vs previous 3-day average
    prev_end = feedback_date - timedelta(days=1)
    prev_start = feedback_date - timedelta(days=3)
    prev_query = select(MessFeedback).where(
        and_(MessFeedback.date >= prev_start, MessFeedback.date <= prev_end)
    )
    if meal:
        prev_query = prev_query.where(MessFeedback.meal == meal)
    if hostel_id is not None:
        prev_query = prev_query.where(MessFeedback.hostel_id == hostel_id)
    prev_result = await db.execute(prev_query)
    prev_feedbacks = prev_result.scalars().all()

    trend = "stable"
    if prev_feedbacks:
        pn = len(prev_feedbacks)
        prev_overall = sum(
            (f.food_quality + f.food_quantity + f.hygiene + f.menu_variety + f.timing) / 5
            for f in prev_feedbacks
        ) / pn
        if overall > prev_overall + 0.2:
            trend = "improving"
        elif overall < prev_overall - 0.2:
            trend = "declining"

    return MessSummaryResponse(
        feedback_date=feedback_date,
        meal=meal,
        avg_food_quality=round(avg_fq, 2),
        avg_food_quantity=round(avg_qty, 2),
        avg_hygiene=round(avg_hyg, 2),
        avg_menu_variety=round(avg_mv, 2),
        avg_timing=round(avg_tim, 2),
        overall_avg=round(overall, 2),
        participation_count=n,
        trend=trend,
    )


# ---------------------------------------------------------------------------
# Alert Logic
# ---------------------------------------------------------------------------

async def check_and_alert(feedback_date: date, db: AsyncSession, hostel_id=None) -> None:
    """
    Checks thresholds for each meal. Creates MessAlert records and sends notifications.
    Called by Celery task `analyze_daily_mess_feedback`.
    """
    from services.notification_service import notify_all_by_role
    from services.hostel_config_service import get_config

    config = await get_config(db, hostel_id)

    for meal in MealPeriod:
        summary = await get_daily_summary(feedback_date, meal, db, hostel_id=hostel_id)
        if summary.participation_count < config.mess_min_responses:
            logger.info(f"Skip alert for {meal.value} — only {summary.participation_count} responses")
            continue

        overall = summary.overall_avg
        if overall < config.mess_critical_threshold:
            alert_type = AlertType.chronic
            threshold_msg = f"avg_overall < {config.mess_critical_threshold} (CRITICAL)"
            notify_roles = [UserRole.mess_manager, UserRole.warden]
        elif overall < config.mess_alert_threshold:
            alert_type = AlertType.spike
            threshold_msg = f"avg_overall < {config.mess_alert_threshold}"
            notify_roles = [UserRole.mess_manager]
        else:
            continue

        # Determine worst dimension for the alert record
        dimensions = {
            MessDimension.food_quality: summary.avg_food_quality,
            MessDimension.food_quantity: summary.avg_food_quantity,
            MessDimension.hygiene: summary.avg_hygiene,
            MessDimension.menu_variety: summary.avg_menu_variety,
            MessDimension.timing: summary.avg_timing,
        }
        worst_dim = min(dimensions, key=dimensions.get)

        alert = MessAlert(
            alert_type=alert_type,
            dimension=worst_dim,
            meal=meal,
            average_score=overall,
            participation_count=summary.participation_count,
            hostel_id=hostel_id,
        )
        db.add(alert)
        await db.commit()

        for role in notify_roles:
            await notify_all_by_role(
                role=role,
                title=f"Mess Alert: {meal.value.capitalize()}",
                body=(
                    f"Average rating {overall:.2f} ({threshold_msg}) "
                    f"based on {summary.participation_count} responses on {feedback_date}."
                ),
                notification_type=NotificationType.mess_alert,
                db=db,
                hostel_id=hostel_id,
            )
        await db.commit()
        logger.info(f"Mess alert created for {meal.value} on {feedback_date} — {threshold_msg}")


async def check_participation_alert(db: AsyncSession, hostel_id=None) -> None:
    """
    Checks if participation was below MESS_MIN_PARTICIPATION for 3 consecutive days.
    Notifies assistant_warden if so.
    """
    from services.notification_service import notify_all_by_role
    from services.hostel_config_service import get_config

    config = await get_config(db, hostel_id)
    today = date.today()
    students_query = select(func.count(User.id)).where(User.role == UserRole.student, User.is_active == True)  # noqa: E712
    if hostel_id is not None:
        students_query = students_query.where(User.hostel_id == hostel_id)
    total_result = await db.execute(students_query)
    total = total_result.scalar() or 0
    if total == 0:
        return

    low_days = 0
    for offset in range(1, 4):
        check_date = today - timedelta(days=offset)
        count_query = select(func.count(MessFeedback.id)).where(MessFeedback.date == check_date)
        if hostel_id is not None:
            count_query = count_query.where(MessFeedback.hostel_id == hostel_id)
        count_result = await db.execute(count_query)
        submissions = count_result.scalar() or 0
        rate = submissions / total
        if rate < config.mess_min_participation:
            low_days += 1
        else:
            break  # not consecutive — stop count

    if low_days >= 3:
        await notify_all_by_role(
            role=UserRole.assistant_warden,
            title="Low Mess Feedback Participation",
            body=(
                f"Mess feedback participation has been below "
                f"{config.mess_min_participation * 100:.0f}% for 3 consecutive days."
            ),
            notification_type=NotificationType.mess_alert,
            db=db,
            hostel_id=hostel_id,
        )
        await db.commit()
        logger.info("Low participation alert sent to assistant_wardens")


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

async def get_recent_alerts(db: AsyncSession, hostel_id=None) -> list[MessAlert]:
    """Returns all alerts from the past 7 days."""
    seven_days_ago = date.today() - timedelta(days=7)
    query = (
        select(MessAlert)
        .where(MessAlert.triggered_at >= func.cast(seven_days_ago, MessAlert.triggered_at.type))
        .order_by(MessAlert.triggered_at.desc())
    )
    if hostel_id is not None:
        query = query.where(MessAlert.hostel_id == hostel_id)
    result = await db.execute(query)
    return result.scalars().all()


async def get_student_feedback(student_id: uuid.UUID, db: AsyncSession) -> list[MessFeedback]:
    """Returns student's feedback from last 30 days."""
    thirty_days_ago = date.today() - timedelta(days=30)
    result = await db.execute(
        select(MessFeedback)
        .where(MessFeedback.student_id == student_id)
        .where(MessFeedback.date >= thirty_days_ago)
        .order_by(MessFeedback.date.desc())
    )
    return result.scalars().all()
