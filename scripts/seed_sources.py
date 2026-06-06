"""
Module: scripts/seed_sources.py
Purpose: Seed source_configs and keywords_master tables
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.db.session (database session)
    - src.db.models (SourceConfig, KeywordMaster)

Used by:
    - Initial deployment
    - Local development
"""

# Standard library
import asyncio
import logging

# Third-party
from sqlalchemy.dialects.postgresql import insert

# Local
from src.db.models import KeywordMaster, SourceConfig
from src.db.session import get_db
from src.logger import setup_logging

logger = logging.getLogger(__name__)

SOURCES: list[dict[str, object]] = [
    {
        "source_key": "supplychaindive",
        "name": "Supply Chain Dive",
        "url": "https://www.supplychaindive.com/",
        "scraper_type": "chain",
        "priority": 10,
    },
    {
        "source_key": "supplychainbrain",
        "name": "SupplyChainBrain",
        "url": "https://www.supplychainbrain.com/",
        "scraper_type": "chain",
        "priority": 20,
    },
    {
        "source_key": "logisticsmgmt",
        "name": "Logistics Management",
        "url": "https://www.logisticsmgmt.com/",
        "scraper_type": "chain",
        "priority": 30,
    },
    {
        "source_key": "manufacturingdive",
        "name": "Manufacturing Dive",
        "url": "https://www.manufacturingdive.com/",
        "scraper_type": "chain",
        "priority": 40,
    },
    {
        "source_key": "foodlogistics",
        "name": "Food Logistics",
        "url": "https://www.foodlogistics.com/",
        "scraper_type": "chain",
        "priority": 50,
    },
    {
        "source_key": "freightwaves",
        "name": "FreightWaves",
        "url": "https://www.freightwaves.com/",
        "scraper_type": "chain",
        "priority": 60,
    },
    {
        "source_key": "scmr",
        "name": "Supply Chain Management Review",
        "url": "https://www.scmr.com/",
        "scraper_type": "chain",
        "priority": 70,
    },
    {
        "source_key": "mhlnews",
        "name": "Material Handling & Logistics",
        "url": "https://www.mhlnews.com/",
        "scraper_type": "chain",
        "priority": 80,
    },
    {
        "source_key": "dcvelocity",
        "name": "DC Velocity",
        "url": "https://www.dcvelocity.com/",
        "scraper_type": "chain",
        "priority": 90,
    },
    {
        "source_key": "supplyon",
        "name": "SupplyOn Blog",
        "url": "https://www.supplyon.com/en/blog/",
        "scraper_type": "chain",
        "priority": 100,
    },
    {
        "source_key": "mit_supply_chain",
        "name": "MIT Supply Chain",
        "url": "https://ctl.mit.edu/news",
        "scraper_type": "chain",
        "priority": 110,
    },
    {
        "source_key": "google_ai",
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/",
        "scraper_type": "chain",
        "priority": 120,
    },
    {
        "source_key": "anthropic_news",
        "name": "Anthropic News",
        "url": "https://www.anthropic.com/news",
        "scraper_type": "chain",
        "priority": 130,
    },
    {
        "source_key": "arxiv_supply_chain_ai",
        "name": "arXiv Supply Chain AI",
        "url": "https://export.arxiv.org/api/query?search_query=all:supply%20chain%20AND%20all:artificial%20intelligence&start=0&max_results=20&sortBy=submittedDate&sortOrder=descending",
        "scraper_type": "arxiv",
        "priority": 140,
    },
]

KEYWORDS: list[dict[str, object]] = [
    {
        "keyword": "supply chain artificial intelligence",
        "tier": 1,
        "weight": 35.0,
        "category": "intersection",
    },
    {
        "keyword": "ai supply chain",
        "tier": 1,
        "weight": 35.0,
        "category": "intersection",
    },
    {
        "keyword": "machine learning logistics",
        "tier": 1,
        "weight": 32.0,
        "category": "intersection",
    },
    {
        "keyword": "pharmaceutical supply chain",
        "tier": 1,
        "weight": 35.0,
        "category": "healthcare",
    },
    {"keyword": "cold chain", "tier": 1, "weight": 30.0, "category": "healthcare"},
    {
        "keyword": "diagnostics supply chain",
        "tier": 1,
        "weight": 35.0,
        "category": "healthcare",
    },
    {"keyword": "supply chain", "tier": 2, "weight": 18.0, "category": "core"},
    {"keyword": "logistics", "tier": 2, "weight": 16.0, "category": "core"},
    {"keyword": "procurement", "tier": 2, "weight": 15.0, "category": "core"},
    {"keyword": "inventory management", "tier": 2, "weight": 16.0, "category": "core"},
    {"keyword": "warehouse automation", "tier": 2, "weight": 18.0, "category": "core"},
    {"keyword": "demand forecasting", "tier": 2, "weight": 18.0, "category": "core"},
    {"keyword": "artificial intelligence", "tier": 2, "weight": 18.0, "category": "ai"},
    {"keyword": "machine learning", "tier": 2, "weight": 17.0, "category": "ai"},
    {"keyword": "generative ai", "tier": 2, "weight": 18.0, "category": "ai"},
    {"keyword": "predictive analytics", "tier": 2, "weight": 16.0, "category": "ai"},
    {"keyword": "resilience", "tier": 3, "weight": 9.0, "category": "signals"},
    {"keyword": "disruption", "tier": 3, "weight": 10.0, "category": "signals"},
    {"keyword": "visibility", "tier": 3, "weight": 8.0, "category": "signals"},
    {"keyword": "risk management", "tier": 3, "weight": 10.0, "category": "signals"},
    {"keyword": "supplier", "tier": 3, "weight": 8.0, "category": "signals"},
    {"keyword": "manufacturing", "tier": 3, "weight": 8.0, "category": "signals"},
    {"keyword": "distribution", "tier": 3, "weight": 8.0, "category": "signals"},
    {"keyword": "planning", "tier": 3, "weight": 7.0, "category": "signals"},
    {"keyword": "automation", "tier": 4, "weight": 5.0, "category": "adjacent"},
    {"keyword": "robotics", "tier": 4, "weight": 5.0, "category": "adjacent"},
    {"keyword": "transportation", "tier": 4, "weight": 5.0, "category": "adjacent"},
    {"keyword": "freight", "tier": 4, "weight": 5.0, "category": "adjacent"},
    {"keyword": "quality", "tier": 4, "weight": 4.0, "category": "adjacent"},
    {"keyword": "regulatory", "tier": 4, "weight": 4.0, "category": "adjacent"},
]


async def seed() -> None:
    """Seed configured sources and keywords idempotently."""
    async with get_db() as session:
        await session.execute(
            insert(SourceConfig)
            .values(SOURCES)
            .on_conflict_do_nothing(
                index_elements=["source_key"],
            ),
        )
        await session.execute(
            insert(KeywordMaster)
            .values(KEYWORDS)
            .on_conflict_do_nothing(
                constraint="uq_keyword_tier",
            ),
        )
    logger.info("Seeded %s sources and %s keywords", len(SOURCES), len(KEYWORDS))


if __name__ == "__main__":
    setup_logging()
    asyncio.run(seed())
