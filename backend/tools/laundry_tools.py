"""
tools/laundry_tools.py — HostelOps AI
========================================
Agent 2 tool callables. All tools are async, call services (not DB directly),
and use Pydantic for typed inputs.
"""
import logging
import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from services import laundry_service
from schemas.enums import MachineStatus

logger = logging.getLogger(__name__)


class GetAvailableSlotsInput(BaseModel):
    slot_date: str  # YYYY-MM-DD


async def get_available_slots_tool(input: GetAvailableSlotsInput, db: AsyncSession):
    """Returns available laundry slots for a given date."""
    from schemas.laundry import LaundrySlotRead
    slots = await laundry_service.get_available_slots(date.fromisoformat(input.slot_date), db)
    return [LaundrySlotRead.model_validate(s) for s in slots]


class BookSlotInput(BaseModel):
    student_id: str
    machine_id: str
    slot_date: str
    slot_time: str


async def book_slot_tool(input: BookSlotInput, db: AsyncSession):
    """Books a laundry slot for the given student."""
    from schemas.laundry import LaundrySlotRead
    slot = await laundry_service.book_slot(
        student_id=uuid.UUID(input.student_id),
        machine_id=uuid.UUID(input.machine_id),
        slot_date=date.fromisoformat(input.slot_date),
        slot_time=input.slot_time,
        db=db,
    )
    return LaundrySlotRead.model_validate(slot)


class CancelSlotInput(BaseModel):
    slot_id: str
    cancelled_by: str
    is_staff: bool = False


async def cancel_slot_tool(input: CancelSlotInput, db: AsyncSession):
    """Cancels a booked slot."""
    from schemas.laundry import LaundrySlotRead
    slot = await laundry_service.cancel_slot(
        slot_id=uuid.UUID(input.slot_id),
        cancelled_by=uuid.UUID(input.cancelled_by),
        is_staff=input.is_staff,
        db=db,
    )
    return LaundrySlotRead.model_validate(slot)


class MarkSlotCompleteInput(BaseModel):
    slot_id: str
    completed_by: str


async def mark_slot_complete_tool(input: MarkSlotCompleteInput, db: AsyncSession):
    """Marks a slot as completed (laundry_man action)."""
    from schemas.laundry import LaundrySlotRead
    slot = await laundry_service.mark_slot_complete(
        slot_id=uuid.UUID(input.slot_id),
        completed_by=uuid.UUID(input.completed_by),
        db=db,
    )
    return LaundrySlotRead.model_validate(slot)


class ReportMachineIssueInput(BaseModel):
    machine_id: str
    issue_description: str
    reported_by: str


async def report_machine_issue_tool(input: ReportMachineIssueInput, db: AsyncSession):
    """Reports a machine issue. Cancels future slots and notifies laundry_man."""
    from schemas.laundry import MachineRead
    machine = await laundry_service.report_machine_issue(
        machine_id=uuid.UUID(input.machine_id),
        issue_description=input.issue_description,
        reported_by=uuid.UUID(input.reported_by),
        db=db,
    )
    return MachineRead.model_validate(machine)
