"""
Module: src/scrapers/chain_scraper.py
Purpose: Scrape sources with native -> Jina -> Apify fallback chain
Author: ScrapeSignal Team
Created: 2026-06-05

Dependencies:
    - src.scrapers.native_scraper
    - src.scrapers.jina_scraper
    - src.scrapers.apify_scraper

Used by:
    - src.scrapers.manager
"""

# Standard library
import logging

# Local
from src.db.models import SourceConfig
from src.scrapers.apify_scraper import ApifyScraper
from src.scrapers.base import BaseScraper, ScrapedArticle
from src.scrapers.jina_scraper import JinaScraper
from src.scrapers.native_scraper import NativeScraper

logger = logging.getLogger(__name__)


class ChainScraper(BaseScraper):
    """Try native scraping first, then Jina, then Apify."""

    def __init__(self) -> None:
        """Initialize chained scrapers."""
        self._providers: list[tuple[str, BaseScraper]] = [
            ("native", NativeScraper()),
            ("jina", JinaScraper()),
            ("apify", ApifyScraper()),
        ]

    async def scrape(self, source: SourceConfig) -> list[ScrapedArticle]:
        """Scrape using the first provider that returns usable content.

        Args:
            source: Source configuration.

        Returns:
            Normalized article candidates.
        """
        errors: list[str] = []
        for provider_name, scraper in self._providers:
            try:
                candidates = await scraper.scrape(source)
                if self._has_usable_content(candidates):
                    logger.info(
                        "Scraper chain used %s for %s (%s articles)",
                        provider_name,
                        source.source_key,
                        len(candidates),
                    )
                    for candidate in candidates:
                        metadata = dict(candidate.get("raw_metadata") or {})
                        metadata["chain_used"] = provider_name
                        candidate["raw_metadata"] = metadata
                    return candidates
                errors.append(f"{provider_name}: no usable content")
            except Exception as error:
                errors.append(f"{provider_name}: {error}")
                logger.warning(
                    "Scraper chain %s failed for %s: %s",
                    provider_name,
                    source.source_key,
                    error,
                )
        logger.error(
            "Scraper chain exhausted for %s: %s",
            source.source_key,
            "; ".join(errors),
        )
        return []

    def _has_usable_content(self, candidates: list[ScrapedArticle]) -> bool:
        """Return whether candidates contain enough text to process.

        Args:
            candidates: Scraped article candidates.

        Returns:
            True when at least one candidate has meaningful body text.
        """
        for candidate in candidates:
            body = str(candidate.get("body") or "").strip()
            if len(body.split()) >= 20:
                return True
        return False
