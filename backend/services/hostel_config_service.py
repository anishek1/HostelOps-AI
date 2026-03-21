"""
services/hostel_config_service.py — HostelOps AI
==================================================
Business logic for reading and updating hostel configuration.
A single DB row stores all operational thresholds.
Falls back to .env settings if no row exists.
Sprint 5: New service.
"""

import logging
import uuid
from datetime import datetime

from cachetools import TTLCache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.hostel_config import HostelConfig

logger = logging.getLogger(__name__)

# In-memory cache: keyed by hostel_id, 5-minute TTL, supports up to 100 hostels
_config_cache: TTLCache = TTLCache(maxsize=100, ttl=300)


def _build_fallback_config() -> HostelConfig:
    """Return a HostelConfig populated from .env settings (not persisted)."""
    return HostelConfig(
        id=uuid.uuid4(),
        hostel_name=settings.HOSTEL_NAME,
        hostel_mode=settings.HOSTEL_MODE,
        total_floors=settings.TOTAL_FLOORS,
        total_students_capacity=settings.TOTAL_STUDENTS_CAPACITY,
        complaint_rate_limit=settings.COMPLAINT_RATE_LIMIT_DAILY,
        approval_queue_timeout_minutes=settings.APPROVAL_QUEUE_TIMEOUT_MINUTES,
        complaint_confidence_threshold=settings.COMPLAINT_CONFIDENCE_THRESHOLD,
        mess_alert_threshold=settings.MESS_ALERT_THRESHOLD,
        mess_critical_threshold=settings.MESS_CRITICAL_THRESHOLD,
        mess_min_participation=settings.MESS_MIN_PARTICIPATION,
        mess_min_responses=settings.MESS_MIN_RESPONSES,
        laundry_slots_start_hour=settings.LAUNDRY_SLOTS_START_HOUR,
        laundry_slots_end_hour=settings.LAUNDRY_SLOTS_END_HOUR,
        laundry_slot_duration_hours=settings.LAUNDRY_SLOT_DURATION_HOURS,
        laundry_noshow_penalty_hours=settings.LAUNDRY_NOSHOW_PENALTY_HOURS,
        laundry_cancellation_deadline_minutes=settings.LAUNDRY_CANCELLATION_DEADLINE_MINUTES,
    )


async def get_config(db: AsyncSession, hostel_id=None) -> HostelConfig:
    """
    Return the hostel config row for the given hostel_id.
    Caches result per hostel_id for 5 minutes.
    Falls back to .env-derived object if no DB row exists (not persisted).
    """
    cache_key = str(hostel_id) if hostel_id is not None else "__legacy__"
    if cache_key in _config_cache:
        return _config_cache[cache_key]

    query = select(HostelConfig)
    if hostel_id is not None:
        query = query.where(HostelConfig.hostel_id == hostel_id)

    result = await db.execute(query)
    config = result.scalar_one_or_none()

    if not config:
        logger.warning(f"No hostel_config row found for hostel_id={hostel_id} — using .env fallback values")
        config = _build_fallback_config()

    _config_cache[cache_key] = config
    return config


async def update_config(updates: dict, db: AsyncSession, hostel_id=None) -> HostelConfig:
    """
    PATCH the hostel config row. Creates one if none exists.
    Invalidates the in-memory cache after update.
    """
    query = select(HostelConfig)
    if hostel_id is not None:
        query = query.where(HostelConfig.hostel_id == hostel_id)
    result = await db.execute(query)
    config = result.scalar_one_or_none()

    if not config:
        config = HostelConfig(id=uuid.uuid4(), hostel_id=hostel_id)
        db.add(config)
        await db.flush()
        logger.info("Created new hostel_config row during update")

    for key, value in updates.items():
        if hasattr(config, key) and value is not None:
            setattr(config, key, value)

    config.updated_at = datetime.utcnow()
    db.add(config)
    await db.commit()
    await db.refresh(config)

    # Invalidate cache so next read gets fresh data
    cache_key = str(hostel_id) if hostel_id is not None else "__legacy__"
    _config_cache.pop(cache_key, None)
    logger.info("Hostel config updated — cache invalidated")
    return config


async def seed_default_config(db: AsyncSession, hostel_id=None) -> HostelConfig | None:
    """
    Create the default hostel_config row if none exists for this hostel.
    Called from create_admin.py (legacy, hostel_id=None) and hostel_service (Sprint 7).
    Idempotent — safe to call multiple times.
    """
    query = select(HostelConfig)
    if hostel_id is not None:
        query = query.where(HostelConfig.hostel_id == hostel_id)

    result = await db.execute(query)
    if result.scalar_one_or_none():
        logger.info("hostel_config row already exists — skipping seed")
        return None

    config = HostelConfig(id=uuid.uuid4(), hostel_id=hostel_id)
    db.add(config)
    await db.flush()
    logger.info(f"Seeded default hostel config row (hostel_id={hostel_id})")
    return config
