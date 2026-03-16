"""
tasks/mess_tasks.py — HostelOps AI
=====================================
Periodic Celery tasks for mess feedback monitoring.
analyze_daily_mess_feedback: runs at 10pm daily (22:00 UTC)
check_participation_alert: runs at 8am daily (08:00 UTC)
Uses asyncio.run() pattern for async DB access from sync Celery tasks.
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
    Triggers Agent 3 to analyze feedback for today.
    Sends alerts if thresholds are crossed.
    """
    async def _run():
        from database import AsyncSessionLocal
        from agents.agent_mess import MessAgent
        async with AsyncSessionLocal() as db:
            today = date.today()
            agent = MessAgent()
            await agent.analyze_daily_feedback(today, db)

    logger.info("[mess_tasks] Running analyze_daily_mess_feedback")
    asyncio.run(_run())
    logger.info("[mess_tasks] analyze_daily_mess_feedback complete")


@celery_app.task(name="tasks.mess_tasks.check_participation_alert")
def check_participation_alert():
    """
    Runs at 8am daily.
    Checks if participation was below 15% for 3 consecutive days.
    Alerts assistant_warden if so.
    """
    async def _run():
        from database import AsyncSessionLocal
        from services.mess_service import check_participation_alert as _check
        async with AsyncSessionLocal() as db:
            await _check(db)

    logger.info("[mess_tasks] Running check_participation_alert")
    asyncio.run(_run())
    logger.info("[mess_tasks] check_participation_alert complete")
