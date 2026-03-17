"""
tasks/laundry_tasks.py — HostelOps AI
========================================
Celery tasks for laundry management.
- process_noshow_penalties: runs hourly, marks overdue booked slots as no_show.
- send_slot_reminders: runs every 30 minutes, sends reminders for upcoming slots.
Sprint 5: New task file.
"""

import asyncio
import logging

from celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop closed")
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


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


@celery_app.task(name="tasks.laundry_tasks.send_slot_reminders", bind=True, max_retries=2)
def send_slot_reminders(self):
    """
    Every-30-minute task: send reminders for slots starting within the next 60 minutes.
    Placeholder implementation — notifies via logger only.
    Full implementation deferred to Sprint 6 (requires slot start-time parsing at scale).
    """
    async def _run():
        from datetime import datetime, timedelta
        from database import AsyncSessionLocal
        from models.laundry_slot import LaundrySlot
        from schemas.enums import LaundrySlotStatus
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            today = datetime.utcnow().date()
            result = await db.execute(
                select(LaundrySlot)
                .where(LaundrySlot.slot_date == today)
                .where(LaundrySlot.booking_status == LaundrySlotStatus.booked)
            )
            slots = result.scalars().all()
            # Filter slots starting in next 30-60 minutes
            now = datetime.utcnow()
            reminder_count = 0
            for slot in slots:
                if not slot.slot_time:
                    continue
                try:
                    start_str = slot.slot_time.split("-")[0]
                    h, m = map(int, start_str.split(":"))
                    slot_start = datetime(today.year, today.month, today.day, h, m)
                    minutes_until = (slot_start - now).total_seconds() / 60
                    if 30 <= minutes_until <= 60 and slot.student_id:
                        from services.notification_service import notify_user
                        from schemas.enums import NotificationType
                        await notify_user(
                            recipient_id=slot.student_id,
                            title="Laundry Slot Reminder",
                            body=f"Your laundry slot starts at {start_str} today. Don't miss it!",
                            notification_type=NotificationType.laundry_reminder,
                            db=db,
                        )
                        reminder_count += 1
                except Exception as e:
                    logger.warning(f"Could not process reminder for slot {slot.id}: {e}")

            logger.info(f"[Celery] Slot reminders: sent {reminder_count} reminders")
            return reminder_count

    try:
        return run_async(_run())
    except Exception as exc:
        logger.error(f"[Celery] send_slot_reminders failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
