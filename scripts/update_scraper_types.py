"""
Module: scripts/update_scraper_types.py
Purpose: Migrate existing source_configs rows to the chain scraper type
Author: ScrapeSignal Team
Created: 2026-06-05

Used by:
    - Post-deploy Neon migration
"""

# Standard library
import asyncio
import logging

# Third-party
from sqlalchemy import text

# Local
from src.db.session import get_db
from src.logger import setup_logging

logger = logging.getLogger(__name__)

UPDATE_SQL = text(
    """
    UPDATE source_configs
    SET scraper_type = 'chain', updated_at = NOW()
    WHERE scraper_type IN ('apify', 'firecrawl', 'jina')
      AND source_key <> 'arxiv_supply_chain_ai'
    """
)


async def migrate() -> None:
    """Update legacy scraper types to the native->Jina->Apify chain."""
    async with get_db() as session:
        result = await session.execute(UPDATE_SQL)
        logger.info("Updated %s source_configs rows to scraper_type=chain", result.rowcount)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(migrate())
