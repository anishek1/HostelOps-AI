"""
services/laundry_service.py — HostelOps AI
============================================
Agent 2 business logic — slot management, fairness algorithm, machine reporting.
Golden Rule 5: No LLM calls here. Golden Rule 4: No business logic in routes.
Golden Rule 16: Always call await db.refresh(obj) after await db.commit().
"""
import logging
import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.laundry_slot import LaundrySlot
from models.machine import Machine
from schemas.enums import LaundrySlotStatus, MachineStatus, NotificationType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Priority Algorithm
# ---------------------------------------------------------------------------

async def calculate_priority_score(student_id: uuid.UUID, db: AsyncSession) -> float:
    """
    Returns a priority score 0.0 – 1.0. Higher = higher priority.
    Algorithm: days since last completed/booked slot, capped to 7-day window.
    New students get max priority (1.0).
    """
    result = await db.execute(
        select(LaundrySlot)
        .where(LaundrySlot.student_id == student_id)
        .where(LaundrySlot.booking_status.in_([LaundrySlotStatus.booked, LaundrySlotStatus.completed]))
        .where(LaundrySlot.slot_date.isnot(None))
        .order_by(LaundrySlot.slot_date.desc())
        .limit(1)
    )
    last = result.scalar_one_or_none()
    if not last or not last.slot_date:
        return 1.0
    days_since = (date.today() - last.slot_date).days
    return min(days_since / 7.0, 1.0)


# ---------------------------------------------------------------------------
# Slot Generation
# ---------------------------------------------------------------------------

async def generate_daily_slots(slot_date: date, db: AsyncSession) -> None:
    """
    Idempotent: generates slots for all operational machines if they don't already exist.
    Slot times run from LAUNDRY_SLOTS_START_HOUR to LAUNDRY_SLOTS_END_HOUR.
    """
    start = settings.LAUNDRY_SLOTS_START_HOUR
    end = settings.LAUNDRY_SLOTS_END_HOUR
    duration = settings.LAUNDRY_SLOT_DURATION_HOURS

    machines_result = await db.execute(
        select(Machine).where(Machine.status == MachineStatus.operational)
    )
    machines = machines_result.scalars().all()

    for machine in machines:
        for hour in range(start, end, duration):
            slot_time = f"{hour:02d}:00-{(hour + duration):02d}:00"
            existing = await db.execute(
                select(LaundrySlot)
                .where(LaundrySlot.machine_id == machine.id)
                .where(LaundrySlot.slot_date == slot_date)
                .where(LaundrySlot.slot_time == slot_time)
            )
            if not existing.scalar_one_or_none():
                slot = LaundrySlot(
                    machine_id=machine.id,
                    slot_date=slot_date,
                    slot_time=slot_time,
                    booking_status=LaundrySlotStatus.available,
                )
                db.add(slot)

    await db.commit()
    logger.info(f"Daily slots ensured for {slot_date}")


# ---------------------------------------------------------------------------
# Slot Queries
# ---------------------------------------------------------------------------

async def get_available_slots(slot_date: date, db: AsyncSession) -> list[LaundrySlot]:
    """Returns available slots for the date, generating them first if needed."""
    await generate_daily_slots(slot_date, db)
    result = await db.execute(
        select(LaundrySlot)
        .where(LaundrySlot.slot_date == slot_date)
        .where(LaundrySlot.booking_status == LaundrySlotStatus.available)
        .order_by(LaundrySlot.machine_id, LaundrySlot.slot_time)
    )
    return result.scalars().all()


async def get_student_bookings(student_id: uuid.UUID, db: AsyncSession) -> list[LaundrySlot]:
    """Returns all upcoming booked slots for a student."""
    result = await db.execute(
        select(LaundrySlot)
        .where(LaundrySlot.student_id == student_id)
        .where(LaundrySlot.booking_status == LaundrySlotStatus.booked)
        .where(LaundrySlot.slot_date >= date.today())
        .order_by(LaundrySlot.slot_date, LaundrySlot.slot_time)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Booking
# ---------------------------------------------------------------------------

async def book_slot(
    student_id: uuid.UUID,
    machine_id: uuid.UUID,
    slot_date: date,
    slot_time: str,
    db: AsyncSession,
) -> LaundrySlot:
    """
    Books a slot. Enforces one-booking-per-day fairness rule.
    Raises ValueError on business rule violations.
    """
    # Fairness: one booking per day
    existing = await db.execute(
        select(LaundrySlot)
        .where(LaundrySlot.student_id == student_id)
        .where(LaundrySlot.slot_date == slot_date)
        .where(LaundrySlot.booking_status == LaundrySlotStatus.booked)
    )
    if existing.scalar_one_or_none():
        raise ValueError("You already have a booking on this date")

    # Check machine is operational
    machine = await db.get(Machine, machine_id)
    if not machine:
        raise ValueError("Machine not found")
    if machine.status != MachineStatus.operational:
        raise ValueError(f"Machine is not operational (status: {machine.status.value})")

    # Fetch the specific available slot
    slot_result = await db.execute(
        select(LaundrySlot)
        .where(LaundrySlot.machine_id == machine_id)
        .where(LaundrySlot.slot_date == slot_date)
        .where(LaundrySlot.slot_time == slot_time)
        .where(LaundrySlot.booking_status == LaundrySlotStatus.available)
    )
    slot = slot_result.scalar_one_or_none()
    if not slot:
        raise ValueError("Slot not available for this machine and time")

    # Assign
    priority = await calculate_priority_score(student_id, db)
    slot.student_id = student_id
    slot.booking_status = LaundrySlotStatus.booked
    slot.priority_score = priority
    slot.booked_at = datetime.utcnow()
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    logger.info(f"Student {student_id} booked slot {slot.id} (priority={priority:.2f})")
    return slot


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------

async def cancel_slot(slot_id: uuid.UUID, cancelled_by: uuid.UUID, is_staff: bool, db: AsyncSession) -> LaundrySlot:
    """
    Cancels a booked slot. Students can only cancel their own.
    Staff (laundry_man, warden) can cancel any.
    """
    slot = await db.get(LaundrySlot, slot_id)
    if not slot:
        raise ValueError("Slot not found")
    if slot.booking_status != LaundrySlotStatus.booked:
        raise ValueError("Only booked slots can be cancelled")
    if not is_staff and slot.student_id != cancelled_by:
        raise PermissionError("You can only cancel your own bookings")

    slot.booking_status = LaundrySlotStatus.available
    slot.student_id = None
    slot.priority_score = None
    slot.booked_at = None
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    logger.info(f"Slot {slot_id} cancelled by user {cancelled_by}")
    return slot


# ---------------------------------------------------------------------------
# Completion
# ---------------------------------------------------------------------------

async def mark_slot_complete(slot_id: uuid.UUID, completed_by: uuid.UUID, db: AsyncSession) -> LaundrySlot:
    """Marks slot as completed. Laundry_man only."""
    slot = await db.get(LaundrySlot, slot_id)
    if not slot:
        raise ValueError("Slot not found")
    if slot.booking_status != LaundrySlotStatus.booked:
        raise ValueError("Only booked slots can be marked complete")

    slot.booking_status = LaundrySlotStatus.completed
    slot.completed_at = datetime.utcnow()
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    logger.info(f"Slot {slot_id} marked complete by {completed_by}")
    return slot


# ---------------------------------------------------------------------------
# Machine Management
# ---------------------------------------------------------------------------

async def get_machine_status(db: AsyncSession) -> list[Machine]:
    """Returns all machines with current status."""
    result = await db.execute(select(Machine))
    return result.scalars().all()


async def create_machine(name: str, floor: int, db: AsyncSession) -> Machine:
    """Creates a new machine. Warden only."""
    machine = Machine(
        name=name,
        floor=floor,
        status=MachineStatus.operational,
        is_active=True,
    )
    db.add(machine)
    await db.commit()
    await db.refresh(machine)
    logger.info(f"Created machine '{name}' on floor {floor}")
    return machine


async def update_machine_status(
    machine_id: uuid.UUID, status: MachineStatus, db: AsyncSession
) -> Machine:
    """Updates machine status. Warden or laundry_man."""
    machine = await db.get(Machine, machine_id)
    if not machine:
        raise ValueError("Machine not found")
    machine.status = status
    machine.updated_at = datetime.utcnow()
    db.add(machine)
    await db.commit()
    await db.refresh(machine)
    logger.info(f"Machine {machine_id} status updated to {status.value}")
    return machine


async def report_machine_issue(
    machine_id: uuid.UUID,
    issue_description: str,
    reported_by: uuid.UUID,
    db: AsyncSession,
) -> Machine:
    """
    Marks machine as under_repair.
    Cancels all future booked slots for this machine.
    Notifies affected students and laundry_man via notification service.
    """
    from services.notification_service import notify_user, notify_all_by_role

    machine = await db.get(Machine, machine_id)
    if not machine:
        raise ValueError("Machine not found")

    machine.status = MachineStatus.under_repair
    machine.last_reported_issue = issue_description
    machine.updated_at = datetime.utcnow()
    db.add(machine)

    # Cancel future booked slots and notify students
    future_slots_result = await db.execute(
        select(LaundrySlot)
        .where(LaundrySlot.machine_id == machine_id)
        .where(LaundrySlot.slot_date >= date.today())
        .where(LaundrySlot.booking_status == LaundrySlotStatus.booked)
    )
    future_slots = future_slots_result.scalars().all()
    cancelled_count = 0
    for slot in future_slots:
        student_id_before_cancel = slot.student_id
        slot.booking_status = LaundrySlotStatus.cancelled
        slot.student_id = None
        db.add(slot)
        if student_id_before_cancel:
            await notify_user(
                recipient_id=student_id_before_cancel,
                title="Laundry Slot Cancelled",
                body=f"Your slot on {slot.slot_date} ({slot.slot_time}) was cancelled due to a machine issue.",
                notification_type=NotificationType.machine_down,
                db=db,
            )
        cancelled_count += 1

    await db.commit()

    # Notify laundry_man role
    await notify_all_by_role(
        role=__import__("schemas.enums", fromlist=["UserRole"]).UserRole.laundry_man,
        title=f"Machine Issue: {machine.name}",
        body=f"Reported by user {reported_by}: {issue_description}",
        notification_type=NotificationType.machine_down,
        db=db,
    )
    await db.commit()

    logger.info(
        f"Machine {machine_id} reported issue by {reported_by}. "
        f"{cancelled_count} slots cancelled."
    )
    return machine
