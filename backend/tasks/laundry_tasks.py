"""
tasks/laundry_tasks.py — HostelOps AI
========================================
Celery tasks for laundry management.
- process_noshow_penalties: runs hourly, marks overdue booked slots as no_show.
- send_slot_reminders: runs every 30 min, notifies students before their slot.
- check_laundry_complaint_clusters: runs every 2h, detects possible machine failures.
"""
import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from celery_app import celery_app
from database import SyncSessionLocal
from schemas.enums import LaundrySlotStatus, NotificationType, ComplaintCategory
from tasks.complaint_tasks import run_async, _create_notification_sync, _get_warden_sync

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.laundry_tasks.process_noshow_penalties", bind=True, max_retries=3)
def process_noshow_penalties(self):
    """
    Hourly task: find booked slots whose date has passed and mark them no_show.
    Sends a notification to each affected student.
    """
    async def _run():
        from database import AsyncSessionLocal
        from services.laundry_service import check_and_apply_noshow_penalties

        async with AsyncSessionLocal() as db:
            count = await check_and_apply_noshow_penalties(db)
            logger.info(f"[Celery] No-show task: processed {count} penalties")
            return count

    try:
        return run_async(_run())
    except Exception as exc:
        logger.error(f"[Celery] process_noshow_penalties failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(name="tasks.laundry_tasks.send_slot_reminders")
def send_slot_reminders():
    """
    Runs every 30 minutes.
    Finds booked slots starting in the next 30 minutes (±5 min window)
    and sends a reminder notification to each student.
    slot_time format: "HH:00-(HH+N):00"  e.g. "08:00-10:00"
    """
    from sqlalchemy import select
    from models.laundry_slot import LaundrySlot

    now_utc = datetime.now(timezone.utc)
    # Window: slots starting between now+25min and now+35min
    window_start = now_utc + timedelta(minutes=25)
    window_end = now_utc + timedelta(minutes=35)
    today = now_utc.date()

    logger.info(f"[slot_reminders] Checking for slots starting {window_start.strftime('%H:%M')}–{window_end.strftime('%H:%M')} UTC")

    reminded = 0
    with SyncSessionLocal() as session:
        try:
            result = session.execute(
                select(LaundrySlot).where(
                    LaundrySlot.slot_date == today,
                    LaundrySlot.booking_status == LaundrySlotStatus.booked,
                    LaundrySlot.student_id.isnot(None),
                )
            )
            slots = result.scalars().all()

            for slot in slots:
                if not slot.slot_time:
                    continue
                # Parse "HH:00-HH:00" → extract start hour
                try:
                    start_str = slot.slot_time.split("-")[0]  # "08:00"
                    slot_hour, slot_minute = int(start_str.split(":")[0]), int(start_str.split(":")[1])
                    slot_dt = datetime(today.year, today.month, today.day, slot_hour, slot_minute, tzinfo=timezone.utc)
                except (ValueError, IndexError):
                    continue

                if window_start <= slot_dt <= window_end:
                    _create_notification_sync(
                        recipient_id=slot.student_id,
                        title="Laundry Slot Starting Soon",
                        body=(
                            f"Your laundry slot starts at {start_str} today. "
                            "Please head to the laundry room now."
                        ),
                        notification_type=NotificationType.laundry_reminder,
                        session=session,
                    )
                    reminded += 1

            session.commit()
            logger.info(f"[slot_reminders] Sent {reminded} reminders")
            return {"status": "ok", "reminded": reminded}

        except Exception as exc:
            session.rollback()
            logger.error(f"[slot_reminders] Unhandled error: {exc}", exc_info=True)
            raise


@celery_app.task(name="tasks.laundry_tasks.check_laundry_complaint_clusters")
def check_laundry_complaint_clusters():
    """
    Runs every 2 hours.
    For each hostel, counts laundry complaints filed in the last 24 hours.
    If the count reaches or exceeds CLUSTER_THRESHOLD (3), alerts the warden —
    a cluster of laundry complaints likely indicates an unreported machine failure.
    Only fires the alert once per 24h window (checks if warden was already notified).
    """
    from sqlalchemy import select, func
    from models.complaint import Complaint
    from models.notification import Notification
    from models.hostel import Hostel

    CLUSTER_THRESHOLD = 3
    window = datetime.now(timezone.utc) - timedelta(hours=24)

    logger.info("[laundry_clusters] Checking for laundry complaint clusters")

    with SyncSessionLocal() as session:
        try:
            # Count laundry complaints per hostel in the last 24h
            rows = session.execute(
                select(Complaint.hostel_id, func.count(Complaint.id).label("cnt"))
                .where(
                    Complaint.category == ComplaintCategory.laundry,
                    Complaint.created_at >= window,
                    Complaint.hostel_id.isnot(None),
                )
                .group_by(Complaint.hostel_id)
                .having(func.count(Complaint.id) >= CLUSTER_THRESHOLD)
            ).all()

            if not rows:
                logger.info("[laundry_clusters] No clusters found")
                return {"status": "ok", "alerts_sent": 0}

            alerts_sent = 0
            for hostel_id, count in rows:
                # Skip if warden already received a cluster alert in the last 24h
                warden_id = _get_warden_sync(session, hostel_id=hostel_id)
                if not warden_id:
                    continue

                already_alerted = session.execute(
                    select(Notification).where(
                        Notification.recipient_id == warden_id,
                        Notification.title == "Possible Machine Failure Detected",
                        Notification.created_at >= window,
                    )
                ).scalar_one_or_none()

                if already_alerted:
                    logger.info(f"[laundry_clusters] Hostel {hostel_id} — already alerted in 24h window")
                    continue

                _create_notification_sync(
                    recipient_id=warden_id,
                    title="Possible Machine Failure Detected",
                    body=(
                        f"{count} laundry complaints have been filed in the last 24 hours. "
                        "This may indicate an unreported machine breakdown. "
                        "Please inspect the laundry room and update machine status if needed."
                    ),
                    notification_type=NotificationType.machine_down,
                    session=session,
                )
                alerts_sent += 1
                logger.info(f"[laundry_clusters] Alert sent for hostel {hostel_id} ({count} complaints)")

            session.commit()
            logger.info(f"[laundry_clusters] Done — {alerts_sent} alerts sent")
            return {"status": "ok", "alerts_sent": alerts_sent}

        except Exception as exc:
            session.rollback()
            logger.error(f"[laundry_clusters] Unhandled error: {exc}", exc_info=True)
            raise
