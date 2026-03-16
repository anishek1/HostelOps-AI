"""
agents/agent_laundry.py — HostelOps AI
=========================================
Agent 2 — Laundry Agent.
Handles laundry complaint routing: machine breakdowns, slot disputes, no-show complaints.
Receives routed complaints from Agent 1 (complaint_tasks.py).
Uses LangChain + Groq, temperature=0. Returns None on failure — never raises.
"""
import logging
import json

from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import settings
from schemas.laundry import LaundryRoutingResult

logger = logging.getLogger(__name__)


class LaundryAgent:
    """
    LangChain-based agent for laundry complaint handling.
    Called by route_to_laundry_agent Celery task when Agent 1 classifies
    a complaint as 'laundry' category.
    """

    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model=settings.GROQ_MODEL_NAME,
            api_key=settings.GROQ_API_KEY,
        )
        # Tools are injected at call-time to avoid import cycles with DB dependency
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are the laundry operations assistant for a student hostel. "
                "Your job is to route laundry complaints correctly:\n"
                "- Machine breakdown → action: reported_machine_issue\n"
                "- Slot booking dispute → action: escalated (assign to laundry_man)\n"
                "- No-show claim → action: escalated (assign to assistant_warden)\n"
                "- General laundry complaint → action: assigned (assign to laundry_man)\n"
                "Always respond with valid JSON: "
                '{"action_taken": "<action>", "assigned_to": "<role or null>", "notes": "<reason>"}'
            ),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    async def route_complaint(self, complaint_text: str, student_id: str) -> LaundryRoutingResult | None:
        """
        Determines routing action for a laundry complaint.
        Returns LaundryRoutingResult or None on failure.
        Does NOT interact with the DB — routing action is stored by the caller.
        """
        try:
            # Use LLM directly without tools for routing decision (no DB needed here)
            response = await self.llm.ainvoke(
                [
                    ("system", self.prompt.messages[0].prompt.template),
                    ("user", f"Student {student_id} filed a laundry complaint: {complaint_text}"),
                ]
            )
            raw = response.content.strip()
            # Try to parse JSON from the response
            data = json.loads(raw)
            result = LaundryRoutingResult(
                action_taken=data.get("action_taken", "assigned"),
                assigned_to=data.get("assigned_to"),
                notes=data.get("notes"),
            )
            logger.info(f"LaundryAgent routed complaint → {result.action_taken}")
            return result
        except Exception as e:
            logger.error(f"LaundryAgent failed for student {student_id}: {e}", exc_info=True)
            # Return a safe default rather than crashing
            return LaundryRoutingResult(
                action_taken="assigned",
                assigned_to="laundry_man",
                notes="Agent failed — defaulted to laundry_man assignment",
            )
