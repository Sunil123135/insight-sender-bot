"""
Module: src/processors/extractor.py
Purpose: Extract normalized article fields from HTML and markdown content
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - beautifulsoup4 (HTML parsing)
    - python-dateutil (date parsing)

Used by:
    - src.scrapers.firecrawl_scraper
    - src.scrapers.jina_scraper
"""

# Standard library
import logging
from datetime import UTC, datetime

# Third-party
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class Extractor:
    """Extract article fields from HTML or text payloads."""

    def from_html(self, html: str, url: str) -> dict[str, object]:
        """Extract article metadata from HTML.

        Args:
            html: Raw HTML string.
            url: Source URL.

        Returns:
            Normalized article candidate dictionary.
        """
        soup = BeautifulSoup(html, "html.parser")
        title = self._first_meta(soup, ["og:title", "twitter:title"]) or self._tag_text(
            soup,
            "title",
        )
        body = self._body_text(soup)
        image_url = self._first_meta(soup, ["og:image", "twitter:image"])
        published_at = self._parse_date(
            self._first_meta(
                soup,
                ["article:published_time", "datePublished", "date"],
            ),
        )
        return {
            "title": title or url,
            "url": url,
            "canonical_url": self._canonical_url(soup),
            "body": body,
            "image_url": image_url,
            "published_at": published_at,
            "raw_metadata": {},
        }

    def from_markdown(
        self, markdown: str, url: str, title: str | None = None
    ) -> dict[str, object]:
        """Extract article fields from markdown/text.

        Args:
            markdown: Markdown or plain text body.
            url: Source URL.
            title: Optional title override.

        Returns:
            Normalized article candidate dictionary.
        """
        lines = [line.strip() for line in markdown.splitlines() if line.strip()]
        inferred_title = title or (lines[0].lstrip("# ").strip() if lines else url)
        return {
            "title": inferred_title[:500],
            "url": url,
            "canonical_url": url,
            "body": "\n".join(lines),
            "image_url": None,
            "published_at": None,
            "raw_metadata": {},
        }

    def _first_meta(self, soup: BeautifulSoup, names: list[str]) -> str | None:
        """Return first matching meta content.

        Args:
            soup: Parsed HTML.
            names: Meta property/name values.

        Returns:
            Meta content if present.
        """
        for name in names:
            tag = soup.find("meta", attrs={"property": name}) or soup.find(
                "meta",
                attrs={"name": name},
            )
            if tag and tag.get("content"):
                return str(tag["content"]).strip()
        return None

    def _tag_text(self, soup: BeautifulSoup, tag_name: str) -> str | None:
        """Return text for the first matching tag.

        Args:
            soup: Parsed HTML.
            tag_name: Tag name.

        Returns:
            Stripped tag text.
        """
        tag = soup.find(tag_name)
        return tag.get_text(" ", strip=True) if tag else None

    def _body_text(self, soup: BeautifulSoup) -> str:
        """Extract readable body text.

        Args:
            soup: Parsed HTML.

        Returns:
            Article-like text.
        """
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        article = soup.find("article") or soup.body or soup
        return article.get_text(" ", strip=True)

    def _canonical_url(self, soup: BeautifulSoup) -> str | None:
        """Extract canonical link.

        Args:
            soup: Parsed HTML.

        Returns:
            Canonical URL if present.
        """
        tag = soup.find("link", attrs={"rel": "canonical"})
        href = tag.get("href") if tag else None
        return str(href).strip() if href else None

    def _parse_date(self, value: str | None) -> datetime | None:
        """Parse date string into UTC datetime.

        Args:
            value: Date string.

        Returns:
            UTC datetime or None.
        """
        if not value:
            return None
        try:
            parsed = date_parser.parse(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except (TypeError, ValueError):
            logger.warning("Could not parse published date: %s", value)
            return None
