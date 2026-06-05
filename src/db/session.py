"""
Module: src/db/session.py
Purpose: Async PostgreSQL engine and session lifecycle management
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src/config.py (settings)
    - sqlalchemy.ext.asyncio (async engine/session)

Used by:
    - src.main (orchestrator)
    - scripts/init_db.py (schema creation)
    - scripts/seed_sources.py (seed data)
"""

# Standard library
import asyncio
import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
# Third-party
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Local
from src.config import settings
from src.db.url import normalize_database_url

logger = logging.getLogger(__name__)

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


engine = create_async_engine(
    normalize_database_url(settings.DATABASE_URL),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=settings.DATABASE_POOL_RECYCLE_SECONDS,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db() -> AsyncIterator[AsyncSession]:
    """Provide a transaction-scoped async database session.

    Yields:
        Async SQLAlchemy session.

    Raises:
        Exception: Re-raises database errors after rollback and logging.
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception("Database transaction failed")
        raise
    finally:
        await session.close()
