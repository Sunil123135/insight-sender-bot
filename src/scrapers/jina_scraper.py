"""
Module: src/scrapers/jina_scraper.py
Purpose: Jina Reader fallback scraper for text extraction
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - httpx (async Jina reader requests)
    - src.processors.extractor (markdown extraction)

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
from src.processors.extractor import Extractor
from src.scrapers.base import BaseScraper, ScrapedArticle
from src.utils.retry import async_retry

logger = logging.getLogger(__name__)


class JinaScraper(BaseScraper):
    """Scrape readable text through Jina Reader."""

    def __init__(self) -> None:
        """Initialize scraper dependencies."""
        self.extractor = Extractor()

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def scrape(self, source: SourceConfig) -> list[ScrapedArticle]:
        """Scrape a source through Jina Reader.

        Args:
            source: Source configuration.

        Returns:
            Normalized article candidates.
        """
        reader_url = f"https://r.jina.ai/http://{source.url.removeprefix('https://').removeprefix('http://')}"
        headers = {"User-Agent": settings.USER_AGENT}
        if settings.secret_is_set(settings.JINA_API_KEY):
            headers["Authorization"] = (
                f"Bearer {settings.JINA_API_KEY.get_secret_value()}"
            )
        timeout = httpx.Timeout(
            settings.SCRAPE_TIMEOUT_SECONDS,
            connect=settings.SCRAPE_CONNECT_TIMEOUT_SECONDS,
        )
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            response = await client.get(reader_url)
            response.raise_for_status()
        article = self.extractor.from_markdown(response.text, source.url)
        article["raw_metadata"] = {"provider": "jina"}
        logger.info(
            "Jina scraped %s characters from %s", len(response.text), source.source_key
        )
        return [article]  # type: ignore[list-item]
