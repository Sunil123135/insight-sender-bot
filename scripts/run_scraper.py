"""
Module: scripts/run_scraper.py
Purpose: Manually run ScrapeSignal scraper manager for selected sources
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.scrapers.manager (scraper orchestration)

Used by:
    - Local validation
"""

# Standard library
import argparse
import asyncio
import logging
import uuid

# Local
from src.db.repository import get_enabled_keywords, get_enabled_sources
from src.db.session import get_db
from src.logger import setup_logging
from src.processors.scorer import RelevanceScorer
from src.scrapers.manager import ScraperManager

logger = logging.getLogger(__name__)


async def run(source_key: str | None, limit: int | None) -> None:
    """Run scraper manager.

    Args:
        source_key: Optional source key filter.
        limit: Optional max source count.
    """
    async with get_db() as session:
        sources = await get_enabled_sources(session)
        if source_key:
            sources = [source for source in sources if source.source_key == source_key]
        if limit:
            sources = sources[:limit]
        keywords = await get_enabled_keywords(session)
        manager = ScraperManager(RelevanceScorer(keywords))
        articles = await manager.scrape_all(
            session, sources, f"manual-{uuid.uuid4().hex[:8]}"
        )
        logger.info("Manual scrape completed articles=%s", len(articles))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=None)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    setup_logging()
    args = parse_args()
    asyncio.run(run(args.source, args.limit))
