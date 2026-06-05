"""
Module: src/scrapers/base.py
Purpose: Abstract scraper contract for ScrapeSignal source adapters
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - abc (abstract base class)
    - src.db.models.py (SourceConfig)

Used by:
    - src.scrapers.firecrawl_scraper
    - src.scrapers.jina_scraper
    - src.scrapers.apify_scraper
    - src.scrapers.arxiv_scraper
"""

# Standard library
from abc import ABC, abstractmethod
from typing import TypedDict

# Local
from src.db.models import SourceConfig


class ScrapedArticle(TypedDict, total=False):
    """Normalized article candidate returned by scrapers."""

    title: str
    url: str
    canonical_url: str | None
    body: str
    image_url: str | None
    author: str | None
    published_at: object | None
    raw_metadata: dict[str, object]


class BaseScraper(ABC):
    """Abstract base class for source scrapers."""

    @abstractmethod
    async def scrape(self, source: SourceConfig) -> list[ScrapedArticle]:
        """Scrape a configured source.

        Args:
            source: Source configuration.

        Returns:
            List of normalized article candidates.
        """
