"""
Module: src/scrapers/arxiv_scraper.py
Purpose: Scrape arXiv Atom feeds and optionally parse linked PDFs
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - httpx (async feed fetch)
    - xml.etree.ElementTree (Atom parsing)
    - src.processors.pdf_parser (PDF extraction)

Used by:
    - src.scrapers.manager
"""

# Standard library
import logging
from datetime import UTC
from typing import Any

import httpx
from dateutil import parser as date_parser

# Third-party
from defusedxml import ElementTree

# Local
from src.config import settings
from src.db.models import SourceConfig
from src.processors.pdf_parser import PDFParser
from src.scrapers.base import BaseScraper, ScrapedArticle
from src.utils.retry import async_retry

logger = logging.getLogger(__name__)

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivScraper(BaseScraper):
    """Scrape arXiv Atom API results."""

    def __init__(self) -> None:
        """Initialize parser dependencies."""
        self.pdf_parser = PDFParser()

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def scrape(self, source: SourceConfig) -> list[ScrapedArticle]:
        """Scrape arXiv Atom feed.

        Args:
            source: Source configuration.

        Returns:
            Normalized article candidates.
        """
        async with httpx.AsyncClient(
            timeout=30.0, headers={"User-Agent": settings.USER_AGENT}
        ) as client:
            response = await client.get(source.url)
            response.raise_for_status()
        root = ElementTree.fromstring(response.text)
        articles: list[ScrapedArticle] = []
        for entry in root.findall("atom:entry", ATOM_NS)[: source.max_articles]:
            articles.append(await self._entry_to_article(entry))
        logger.info("Parsed %s arXiv entries", len(articles))
        return articles

    async def _entry_to_article(self, entry: Any) -> ScrapedArticle:
        """Convert Atom entry to article candidate.

        Args:
            entry: Atom entry element.

        Returns:
            Scraped article.
        """
        title = self._text(entry, "atom:title")
        summary = self._text(entry, "atom:summary")
        url = self._text(entry, "atom:id")
        pdf_url = self._pdf_url(entry)
        body = summary
        if pdf_url:
            try:
                body = await self.pdf_parser.extract_text_from_url(pdf_url)
            except Exception as error:
                logger.warning("arXiv PDF parse failed for %s: %s", pdf_url, error)
        return {
            "title": title,
            "url": url,
            "canonical_url": url,
            "body": body,
            "image_url": None,
            "author": self._author(entry),
            "published_at": self._published(entry),
            "raw_metadata": {"provider": "arxiv", "pdf_url": pdf_url},
        }

    def _text(self, entry: Any, path: str) -> str:
        """Extract text from an Atom child.

        Args:
            entry: Atom entry.
            path: Namespace-aware child path.

        Returns:
            Text value.
        """
        node = entry.find(path, ATOM_NS)
        return " ".join((node.text or "").split()) if node is not None else ""

    def _author(self, entry: Any) -> str | None:
        """Extract first author name.

        Args:
            entry: Atom entry.

        Returns:
            Author name.
        """
        node = entry.find("atom:author/atom:name", ATOM_NS)
        return " ".join((node.text or "").split()) if node is not None else None

    def _published(self, entry: Any) -> object | None:
        """Parse published timestamp.

        Args:
            entry: Atom entry.

        Returns:
            UTC datetime or None.
        """
        value = self._text(entry, "atom:published")
        if not value:
            return None
        return date_parser.parse(value).astimezone(UTC)

    def _pdf_url(self, entry: Any) -> str | None:
        """Extract arXiv PDF link.

        Args:
            entry: Atom entry.

        Returns:
            PDF URL.
        """
        for link in entry.findall("atom:link", ATOM_NS):
            if link.attrib.get("title") == "pdf":
                href = link.attrib.get("href")
                return str(href) if href else None
        return None
