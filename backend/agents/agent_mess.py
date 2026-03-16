"""
agents/agent_mess.py — HostelOps AI
======================================
Agent 3 — Mess Feedback Agent.
Collects feedback summaries and crafts alert messages for wardens/mess managers.
Called by Celery beat task daily at 10pm. Returns None on failure — never raises.
"""
import logging
from datetime import date

from langchain_groq import ChatGroq

from config import settings

logger = logging.getLogger(__name__)


class MessAgent:
    """
    LangChain-based agent for mess feedback analysis.
    The core threshold logic lives in mess_service.check_and_alert().
    This agent's role is to craft human-readable alert messages when thresholds are crossed.
    """

    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model=settings.GROQ_MODEL_NAME,
            api_key=settings.GROQ_API_KEY,
        )

    async def analyze_daily_feedback(self, feedback_date: date, db) -> None:
        """
        Called by Celery task. Runs threshold checks via mess_service.
        The service handles alert creation and notification sending.
        Agent adds an LLM-generated summary message where thresholds are crossed.
        """
        from services.mess_service import check_and_alert, check_participation_alert

        try:
            # Core threshold check — service handles DB and notifications
            await check_and_alert(feedback_date, db)
            await check_participation_alert(db)
            logger.info(f"MessAgent completed daily analysis for {feedback_date}")
        except Exception as e:
            logger.error(f"MessAgent.analyze_daily_feedback failed: {e}", exc_info=True)
            # Never re-raise — let Celery task mark as success anyway

    async def generate_alert_summary(self, meal: str, avg_rating: float, participation: int) -> str:
        """
        Uses LLM to generate a human-friendly alert message.
        Called optionally by services when creating alerts.
        Returns a plain string. Returns default message on failure.
        """
        try:
            response = await self.llm.ainvoke(
                [
                    (
                        "system",
                        "You write short (2-sentence) operational alerts for hostel wardens. "
                        "Be factual and actionable. No pleasantries."
                    ),
                    (
                        "user",
                        f"The {meal} today received an average rating of {avg_rating:.1f}/5 "
                        f"from {participation} students. Write an alert message."
                    ),
                ]
            )
            return response.content.strip()
        except Exception as e:
            logger.error(f"MessAgent.generate_alert_summary failed: {e}")
            return (
                f"Mess alert: {meal} rated {avg_rating:.1f}/5 by {participation} students. "
                "Please investigate."
            )
