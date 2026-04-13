"""
tasks/mess_tasks.py — HostelOps AI
=====================================
Periodic Celery tasks for mess feedback monitoring.
analyze_daily_mess_feedback: runs at 10pm daily.
check_participation_alert: runs daily at 8am.
Calls mess_service functions directly — no MessAgent wrapper needed.
"""
import asyncio
import logging
from datetime import date

from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.mess_tasks.analyze_daily_mess_feedback")
def analyze_daily_mess_feedback():
    """
    Runs at 10pm daily.
    Checks mess feedback thresholds and sends alerts if crossed.
    """
    async def _run():
        from database import AsyncSessionLocal
        from services.mess_service import check_and_alert
        async with AsyncSessionLocal() as db:
            today = date.today()
            await check_and_alert(today, db)

    logger.info("[mess_tasks] Running analyze_daily_mess_feedback")
    asyncio.run(_run())
    logger.info("[mess_tasks] analyze_daily_mess_feedback complete")


@celery_app.task(name="tasks.mess_tasks.check_participation_alert")
def check_participation_alert():
    """
    Runs at 8am daily.
    Checks if participation was below threshold for 3 consecutive days.
    Alerts warden if so.
    """
    async def _run():
        from database import AsyncSessionLocal
        from services.mess_service import check_participation_alert as _check
        async with AsyncSessionLocal() as db:
            await _check(db)

    logger.info("[mess_tasks] Running check_participation_alert")
    asyncio.run(_run())
    logger.info("[mess_tasks] check_participation_alert complete")
