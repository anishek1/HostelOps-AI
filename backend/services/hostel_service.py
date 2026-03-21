"""
services/hostel_service.py — HostelOps AI
============================================
Business logic for hostel creation and lookup.
Sprint 7: Multi-tenant architecture.
"""
import logging
import random
import string

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.hostel import Hostel
from schemas.enums import HostelMode, UserRole

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

def _generate_code() -> str:
    """Generate a random hostel code in the format XXXX-0000 (e.g. IGBH-4821)."""
    letters = "".join(random.choices(string.ascii_uppercase, k=4))
    digits = "".join(random.choices(string.digits, k=4))
    return f"{letters}-{digits}"


async def generate_unique_hostel_code(db: AsyncSession) -> str:
    """Generate a hostel code guaranteed to be unique in the DB."""
    for _ in range(10):  # retry up to 10 times (collision probability is negligible)
        code = _generate_code()
        result = await db.execute(select(Hostel).where(Hostel.code == code))
        if result.scalar_one_or_none() is None:
            return code
    raise RuntimeError("Failed to generate a unique hostel code after 10 attempts.")


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------

async def get_hostel_by_code(code: str, db: AsyncSession) -> Hostel | None:
    """Return the Hostel with the given code, or None if not found."""
    result = await db.execute(select(Hostel).where(Hostel.code == code.upper()))
    return result.scalar_one_or_none()


async def get_hostel_by_id(hostel_id: str, db: AsyncSession) -> Hostel | None:
    """Return the Hostel with the given UUID, or None if not found."""
    return await db.get(Hostel, hostel_id)


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------

async def create_hostel_with_warden(payload, db: AsyncSession):
    """
    Creates a Hostel record + the first warden (assistant_warden) user account.
    The warden account is immediately verified and active — no approval needed.
    Returns (hostel, user, access_token, refresh_token).
    """
    from models.user import User
    from schemas.enums import HostelMode
    from services.auth_service import (
        hash_password,
        create_access_token,
        create_refresh_token_db,
    )
    from services.hostel_config_service import seed_default_config

    # 1. Generate unique hostel code
    code = await generate_unique_hostel_code(db)

    # 2. Create hostel
    hostel = Hostel(
        name=payload.hostel_name,
        code=code,
        mode=payload.hostel_mode,
        total_floors=payload.total_floors,
        total_students_capacity=payload.total_students_capacity,
    )
    db.add(hostel)
    await db.flush()  # get hostel.id before creating user

    # 3. Check warden room_number not already taken
    from sqlalchemy import select as _select
    existing = await db.execute(
        _select(User).where(User.room_number == payload.warden_room_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this room number already exists.",
        )

    # 4. Create warden user — immediately verified
    warden = User(
        name=payload.warden_name,
        room_number=payload.warden_room_number,
        role=UserRole.assistant_warden,
        hostel_mode=payload.hostel_mode,
        hashed_password=hash_password(payload.warden_password),
        is_verified=True,
        is_active=True,
        hostel_id=hostel.id,
    )
    db.add(warden)
    await db.flush()  # get warden.id

    # 5. Seed default hostel config for this hostel
    await seed_default_config(db, hostel_id=hostel.id)

    await db.commit()
    await db.refresh(hostel)
    await db.refresh(warden)

    # 6. Issue tokens
    token_data = {"sub": str(warden.id), "role": warden.role.value}
    access_token = create_access_token(token_data)
    refresh_token = await create_refresh_token_db(str(warden.id), None, db)

    logger.info(f"Hostel '{hostel.name}' created with code {hostel.code} by warden {warden.id}")
    return hostel, warden, access_token, refresh_token
