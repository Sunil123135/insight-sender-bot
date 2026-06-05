"""
Module: src/scrapers/apify_scraper.py
Purpose: Apify dataset scraper for complex JavaScript-heavy sources
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - httpx (async Apify API calls)

Used by:
    - src.scrapers.manager
"""

# Standard library
import logging

# Third-party
import httpx

# Local
from src.config import settings
from src.db.models import SourceConfig
from src.scrapers.base import BaseScraper, ScrapedArticle
from src.utils.retry import async_retry

logger = logging.getLogger(__name__)


class ApifyScraper(BaseScraper):
    """Fetch article-like records from an Apify actor task dataset."""

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def scrape(self, source: SourceConfig) -> list[ScrapedArticle]:
        """Scrape source through Apify if token and task metadata exist.

        Args:
            source: Source configuration.

        Returns:
            Normalized article candidates.
        """
        if not settings.secret_is_set(settings.APIFY_API_TOKEN):
            logger.warning("APIFY_API_TOKEN missing; skipping %s", source.source_key)
            return []
        task_id = (
            source.raw_metadata.get("apify_task_id")
            if hasattr(source, "raw_metadata")
            else None
        )
        if not task_id:
            logger.warning("No Apify task configured for %s", source.source_key)
            return []
        url = f"https://api.apify.com/v2/actor-tasks/{task_id}/runs/last/dataset/items"
        params = {"token": settings.APIFY_API_TOKEN.get_secret_value(), "clean": "true"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            rows = response.json()
        return [self._normalize(row, source) for row in rows[: source.max_articles]]

    def _normalize(
        self, row: dict[str, object], source: SourceConfig
    ) -> ScrapedArticle:
        """Normalize an Apify dataset item.

        Args:
            row: Dataset item.
            source: Source configuration.

        Returns:
            Scraped article candidate.
        """
        return {
            "title": str(row.get("title") or row.get("headline") or source.name),
            "url": str(row.get("url") or source.url),
            "canonical_url": str(row.get("url") or source.url),
            "body": str(row.get("text") or row.get("description") or ""),
            "image_url": str(row.get("imageUrl") or "") or None,
            "author": str(row.get("author") or "") or None,
            "published_at": None,
            "raw_metadata": {"provider": "apify", "item": row},
        }
