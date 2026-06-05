"""
Module: scripts/init_db.py
Purpose: Initialize ScrapeSignal PostgreSQL schema
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.db.session (async engine)
    - src.db.models (metadata)

Used by:
    - Manual setup
    - Deployment initialization
"""

# Standard library
import asyncio
import logging

# Local
from src.db.models import Base
from src.db.session import engine
from src.logger import setup_logging

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Create all ScrapeSignal database tables."""
    logger.info("Initializing database schema")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized")


if __name__ == "__main__":
    setup_logging()
    asyncio.run(init_db())
