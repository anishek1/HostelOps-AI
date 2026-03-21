"""
routes/laundry.py — HostelOps AI
=====================================
Laundry slot booking and machine management endpoints.
Thin routes — all logic in services/laundry_service.py.
"""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List

from database import get_db
from models.machine import Machine
from models.user import User
from schemas.laundry import (
    LaundryBookingResponse,
    LaundrySlotCreate,
    LaundrySlotRead,
    MachineCreate,
    MachineRead,
    MachineStatusUpdate,
)
from schemas.enums import UserRole
from services.auth_service import get_current_user, require_role
from services import laundry_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Warden-level roles for machine management (Golden Rule 19)
WARDEN_ROLES = [UserRole.assistant_warden, UserRole.warden, UserRole.chief_warden]


# ---------------------------------------------------------------------------
# Slot Routes
# ---------------------------------------------------------------------------

@router.get("/slots", response_model=List[LaundrySlotRead])
async def get_slots(
    slot_date: date = Query(..., description="Date in YYYY-MM-DD format"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all available laundry slots for a given date."""
    slots = await laundry_service.get_available_slots(slot_date, db)
    return [LaundrySlotRead.model_validate(s) for s in slots[offset:offset + limit]]


@router.post("/slots/book", response_model=LaundryBookingResponse)
async def book_slot(
    booking: LaundrySlotCreate,
    current_user: User = Depends(require_role(UserRole.student)),
    db: AsyncSession = Depends(get_db),
):
    """Book a laundry slot (students only)."""
    try:
        slot = await laundry_service.book_slot(
            student_id=current_user.id,
            machine_id=uuid.UUID(booking.machine_id),
            slot_date=booking.slot_date,
            slot_time=booking.slot_time,
            db=db,
        )
        machine = await db.get(Machine, slot.machine_id)
        return LaundryBookingResponse(
            slot_id=str(slot.id),
            machine_name=machine.name if machine else "Unknown",
            slot_date=slot.slot_date,
            slot_time=slot.slot_time,
            booking_status=slot.booking_status,
            message="Booking successful",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/slots/{slot_id}")
async def cancel_slot(
    slot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a booked slot. Students cancel their own; staff cancel any."""
    try:
        is_staff = current_user.role in WARDEN_ROLES or current_user.role == UserRole.laundry_man
        await laundry_service.cancel_slot(
            slot_id=uuid.UUID(slot_id),
            cancelled_by=current_user.id,
            is_staff=is_staff,
            db=db,
        )
        return {"message": "Slot cancelled successfully"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-bookings", response_model=List[LaundrySlotRead])
async def my_bookings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(UserRole.student)),
    db: AsyncSession = Depends(get_db),
):
    """Get upcoming booked slots for the current student."""
    bookings = await laundry_service.get_student_bookings(current_user.id, db)
    return [LaundrySlotRead.model_validate(b) for b in bookings[offset:offset + limit]]


@router.patch("/slots/{slot_id}/complete")
async def mark_complete(
    slot_id: str,
    current_user: User = Depends(require_role(UserRole.laundry_man)),
    db: AsyncSession = Depends(get_db),
):
    """Mark a slot as completed (laundry_man only)."""
    try:
        slot = await laundry_service.mark_slot_complete(
            slot_id=uuid.UUID(slot_id),
            completed_by=current_user.id,
            db=db,
        )
        return {"message": "Slot marked as completed", "slot_id": str(slot.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Machine Routes
# ---------------------------------------------------------------------------

@router.get("/machines", response_model=List[MachineRead])
async def get_machines(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all laundry machines with their current status."""
    machines = await laundry_service.get_machine_status(db)
    return [MachineRead.model_validate(m) for m in machines]


@router.patch("/machines/{machine_id}/status")
async def update_machine_status(
    machine_id: str,
    update: MachineStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update machine status (warden or laundry_man only)."""
    if current_user.role not in WARDEN_ROLES and current_user.role != UserRole.laundry_man:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        machine = await laundry_service.update_machine_status(
            machine_id=uuid.UUID(machine_id),
            status=update.status,
            db=db,
        )
        return MachineRead.model_validate(machine)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/machines", response_model=MachineRead)
async def create_machine(
    machine_data: MachineCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new laundry machine (warden only)."""
    if current_user.role not in WARDEN_ROLES:
        raise HTTPException(status_code=403, detail="Only wardens can add machines")
    machine = await laundry_service.create_machine(
        name=machine_data.name,
        floor=machine_data.floor,
        db=db,
    )
    return MachineRead.model_validate(machine)
