"""
Module: src/scrapers/firecrawl_scraper.py
Purpose: Firecrawl-backed scraper for primary industry sources
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - httpx (async Firecrawl API calls)
    - src.processors.extractor (HTML/markdown extraction)

Used by:
    - src.scrapers.manager
"""

# Standard library
import logging
from urllib.parse import urljoin

# Third-party
import httpx

# Local
from src.config import settings
from src.db.models import SourceConfig
from src.processors.extractor import Extractor
from src.scrapers.base import BaseScraper, ScrapedArticle
from src.utils.retry import async_retry

logger = logging.getLogger(__name__)

FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v1/scrape"
FIRECRAWL_MAP_URL = "https://api.firecrawl.dev/v1/map"


class FirecrawlScraper(BaseScraper):
    """Scrape websites using Firecrawl map and scrape endpoints."""

    def __init__(self) -> None:
        """Initialize scraper dependencies."""
        self.extractor = Extractor()

    async def scrape(self, source: SourceConfig) -> list[ScrapedArticle]:
        """Scrape a source through Firecrawl.

        Args:
            source: Source configuration.

        Returns:
            Normalized article candidates.
        """
        if not settings.secret_is_set(settings.FIRECRAWL_API_KEY):
            logger.warning(
                "FIRECRAWL_API_KEY missing; using direct fallback for %s",
                source.source_key,
            )
            return await self._direct_fallback(source)

        urls = await self._map_urls(source)
        candidates: list[ScrapedArticle] = []
        for url in urls[: source.max_articles]:
            try:
                candidates.append(await self._scrape_url(url))
            except Exception as error:
                logger.warning("Firecrawl URL scrape failed for %s: %s", url, error)
        return candidates

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def _map_urls(self, source: SourceConfig) -> list[str]:
        """Map source URLs through Firecrawl.

        Args:
            source: Source configuration.

        Returns:
            Candidate URLs.
        """
        headers = {
            "Authorization": f"Bearer {settings.FIRECRAWL_API_KEY.get_secret_value()}"
        }
        payload = {"url": source.url, "limit": source.max_articles}
        async with httpx.AsyncClient(timeout=self._timeout()) as client:
            response = await client.post(
                FIRECRAWL_MAP_URL, json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()
        links = data.get("links") or data.get("data") or []
        urls = [
            str(link.get("url", link)) if isinstance(link, dict) else str(link)
            for link in links
        ]
        return [urljoin(source.url, url) for url in urls if url]

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def _scrape_url(self, url: str) -> ScrapedArticle:
        """Scrape one URL through Firecrawl.

        Args:
            url: Article URL.

        Returns:
            Normalized candidate.
        """
        headers = {
            "Authorization": f"Bearer {settings.FIRECRAWL_API_KEY.get_secret_value()}"
        }
        payload = {"url": url, "formats": ["markdown", "html"]}
        async with httpx.AsyncClient(timeout=self._timeout()) as client:
            response = await client.post(
                FIRECRAWL_SCRAPE_URL, json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json().get("data", response.json())
        markdown = str(data.get("markdown") or "")
        html = str(data.get("html") or "")
        candidate = (
            self.extractor.from_markdown(markdown, url)
            if markdown
            else self.extractor.from_html(html, url)
        )
        candidate["raw_metadata"] = {"provider": "firecrawl"}
        return candidate  # type: ignore[return-value]

    async def _direct_fallback(self, source: SourceConfig) -> list[ScrapedArticle]:
        """Fetch homepage directly when Firecrawl credentials are absent.

        Args:
            source: Source configuration.

        Returns:
            One extracted candidate from source homepage.
        """
        async with httpx.AsyncClient(
            timeout=self._timeout(), headers={"User-Agent": settings.USER_AGENT}
        ) as client:
            response = await client.get(source.url)
            response.raise_for_status()
        return [self.extractor.from_html(response.text, source.url)]  # type: ignore[list-item]

    def _timeout(self) -> httpx.Timeout:
        """Build HTTP timeout.

        Returns:
            Configured timeout.
        """
        return httpx.Timeout(
            settings.SCRAPE_TIMEOUT_SECONDS,
            connect=settings.SCRAPE_CONNECT_TIMEOUT_SECONDS,
        )
