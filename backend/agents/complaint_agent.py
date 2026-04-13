"""
agents/complaint_agent.py — HostelOps AI
==========================================
Real tool-calling agent for actionable complaints (laundry, maintenance,
multi-person affected). Uses Groq function calling with a ReAct loop.

Triggered by the classify_and_route_complaint Celery task AFTER the
classification pipeline completes, only when:
  - category is laundry or maintenance
  - OR affected_count > 1

The agent can call up to 5 tools per complaint before terminating.
It never changes complaint status directly — all state changes go through
the services (which enforce the state machine).
"""
import json
import logging
from typing import Any

from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5

# ---------------------------------------------------------------------------
# Tool schemas — passed to Groq as function definitions
# ---------------------------------------------------------------------------

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_student_complaint_history",
            "description": (
                "Retrieve the student's recent complaint history in this hostel. "
                "Use this to detect repeat complaints about the same issue."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "UUID of the student"},
                    "hostel_id": {"type": "string", "description": "UUID of the hostel"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["student_id", "hostel_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_similar_open_complaints",
            "description": (
                "Find open complaints with the same category and optional location. "
                "Use to detect duplicate or related issues already being tracked."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "hostel_id": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": ["mess", "laundry", "maintenance", "interpersonal", "critical", "uncategorised"],
                    },
                    "location": {"type": "string", "description": "Optional: extracted location from complaint"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["hostel_id", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_staff_availability",
            "description": "Get active staff members with a given role in the hostel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "enum": ["laundry_man", "mess_staff", "warden"],
                        "description": "The role to search for",
                    },
                    "hostel_id": {"type": "string"},
                },
                "required": ["role", "hostel_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_machine_status",
            "description": (
                "Check whether a specific laundry machine is operational. "
                "Use for laundry complaints that mention a specific machine."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_id": {"type": "string", "description": "UUID of the machine"},
                    "hostel_id": {"type": "string"},
                },
                "required": ["machine_id", "hostel_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_complaint",
            "description": (
                "Escalate a complaint directly to the warden when it is urgent, "
                "affects many students, or poses a safety risk. "
                "Only use when the situation clearly warrants immediate warden attention."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "complaint_id": {"type": "string"},
                    "reason": {"type": "string", "description": "Clear reason for escalation"},
                    "hostel_id": {"type": "string"},
                },
                "required": ["complaint_id", "reason", "hostel_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_affected_slots",
            "description": (
                "Cancel upcoming booked laundry slots for a broken machine "
                "and notify affected students to rebook. "
                "Use only when a machine is confirmed to be non-operational."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_id": {"type": "string"},
                    "hostel_id": {"type": "string"},
                },
                "required": ["machine_id", "hostel_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "notify_student",
            "description": "Send a direct notification to the student who filed the complaint.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "notification_type": {
                        "type": "string",
                        "enum": [
                            "complaint_assigned", "approval_needed", "laundry_reminder",
                            "machine_down", "complaint_escalated",
                        ],
                        "default": "complaint_assigned",
                    },
                },
                "required": ["student_id", "title", "body"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Tool dispatch — maps tool name → async function
# ---------------------------------------------------------------------------

async def _dispatch_tool(
    name: str, arguments: dict, db: AsyncSession
) -> dict:
    """Execute a tool by name and return its result as a dict."""
    from tools.complaint_tools import (
        GetComplaintHistoryInput,
        FindSimilarInput,
        GetStaffInput,
        CheckMachineInput,
        EscalateInput,
        RescheduleInput,
        NotifyStudentInput,
        get_student_complaint_history,
        find_similar_open_complaints,
        get_staff_availability,
        check_machine_status,
        escalate_complaint_agent,
        reschedule_affected_slots,
        notify_student_tool,
    )
    from schemas.enums import ComplaintCategory

    if name == "get_student_complaint_history":
        result = await get_student_complaint_history(
            GetComplaintHistoryInput(**arguments), db
        )
    elif name == "find_similar_open_complaints":
        # category comes in as a string; convert to enum
        arguments["category"] = ComplaintCategory(arguments["category"])
        result = await find_similar_open_complaints(
            FindSimilarInput(**arguments), db
        )
    elif name == "get_staff_availability":
        result = await get_staff_availability(GetStaffInput(**arguments), db)
    elif name == "check_machine_status":
        result = await check_machine_status(CheckMachineInput(**arguments), db)
    elif name == "escalate_complaint":
        result = await escalate_complaint_agent(EscalateInput(**arguments), db)
    elif name == "reschedule_affected_slots":
        result = await reschedule_affected_slots(RescheduleInput(**arguments), db)
    elif name == "notify_student":
        result = await notify_student_tool(NotifyStudentInput(**arguments), db)
    else:
        return {"error": f"Unknown tool: {name}"}

    return result.model_dump()


# ---------------------------------------------------------------------------
# Agent system prompt
# ---------------------------------------------------------------------------

AGENT_SYSTEM_PROMPT = """You are a hostel operations AI agent for an Indian college hostel.
You have been triggered because a complaint requires active intervention.

Your job is to take real, concrete actions using the tools available to you.
Think step-by-step. Use tools to gather information before deciding.

Guidelines:
- For laundry complaints: check machine status, look for similar open complaints,
  reschedule slots if machine is broken, notify student.
- For maintenance complaints affecting many students: check for similar complaints,
  escalate if safety risk or >3 students affected.
- For any complaint: check student history to detect repeat issues.
  Escalate if this is the 3rd+ complaint about the same topic in 7 days.
- Do NOT escalate unless clearly warranted. Unnecessary escalations waste warden time.
- Always notify the student about the action taken.
- Stop after taking all appropriate actions. Do not loop unnecessarily.

You will receive complaint context as the first user message. Use it to decide actions.
"""


# ---------------------------------------------------------------------------
# Main agent entrypoint
# ---------------------------------------------------------------------------

async def run_complaint_agent(
    complaint_id: str,
    student_id: str,
    hostel_id: str,
    category: str,
    severity: str,
    affected_count: int,
    location: str | None,
    safety_flag: bool,
    complaint_text: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """
    Runs the Groq tool-calling agent for a complaint.
    Returns a summary dict describing what actions were taken.
    Never raises — catches all errors and logs them.
    """
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    # Build the initial context message for the agent
    context = (
        f"Complaint ID: {complaint_id[:8].upper()}\n"
        f"Category: {category}\n"
        f"Severity: {severity}\n"
        f"Affected students: {affected_count}\n"
        f"Location: {location or 'unspecified'}\n"
        f"Safety flag: {safety_flag}\n"
        f"Student ID: {student_id}\n"
        f"Hostel ID: {hostel_id}\n\n"
        f"Complaint text:\n{complaint_text}"
    )

    messages: list[dict] = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": context},
    ]

    actions_taken: list[str] = []
    iterations = 0

    logger.info(f"[complaint_agent] Starting agent for complaint {complaint_id}")

    try:
        while iterations < MAX_ITERATIONS:
            iterations += 1

            response = await client.chat.completions.create(
                model=settings.GROQ_MODEL_NAME,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0,
            )

            msg = response.choices[0].message

            # No tool calls — agent is done
            if not msg.tool_calls:
                logger.info(
                    f"[complaint_agent] Agent finished after {iterations} iterations. "
                    f"Actions: {actions_taken}"
                )
                return {
                    "status": "completed",
                    "iterations": iterations,
                    "actions_taken": actions_taken,
                    "final_message": msg.content or "",
                }

            # Append assistant message with tool calls
            messages.append(msg)

            # Execute each tool call
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    arguments = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                logger.info(f"[complaint_agent] Calling tool: {tool_name}({arguments})")

                try:
                    result = await _dispatch_tool(tool_name, arguments, db)
                    result_str = json.dumps(result)
                    actions_taken.append(f"{tool_name}: {result_str[:120]}")
                except Exception as tool_err:
                    result_str = json.dumps({"error": str(tool_err)})
                    logger.error(f"[complaint_agent] Tool {tool_name} failed: {tool_err}")

                # Append tool result back to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                })

        # Hit iteration cap
        logger.warning(
            f"[complaint_agent] Reached max iterations ({MAX_ITERATIONS}) "
            f"for complaint {complaint_id}"
        )
        return {
            "status": "max_iterations_reached",
            "iterations": iterations,
            "actions_taken": actions_taken,
        }

    except Exception as exc:
        logger.error(
            f"[complaint_agent] Unhandled error for complaint {complaint_id}: {exc}",
            exc_info=True,
        )
        return {
            "status": "error",
            "error": str(exc),
            "actions_taken": actions_taken,
        }
