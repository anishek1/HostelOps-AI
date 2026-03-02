"""
database.py — HostelOps AI
==========================
Async SQLAlchemy engine, session factory, and declarative Base.
Import `get_db` as a FastAPI dependency in route handlers.
Import `Base` in every model file.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

# Create async engine from DATABASE_URL in config.py
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,          # Set True locally to log SQL; False in production
    pool_pre_ping=True,  # Reconnect on stale connections
    pool_size=10,
    max_overflow=20,
)

# Session factory — yields async sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """
    FastAPI dependency. Yields an AsyncSession and guarantees cleanup.
    Usage in routes:
        async def my_route(db: AsyncSession = Depends(get_db)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Sync engine — for Celery tasks ONLY
# ---------------------------------------------------------------------------
# Celery workers cannot use async SQLAlchemy sessions.
# Use SyncSessionLocal() exclusively inside Celery task functions.
# Never use this in FastAPI routes or services.

from sqlalchemy import create_engine          # noqa: E402
from sqlalchemy.orm import sessionmaker        # noqa: E402

sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2"),
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

