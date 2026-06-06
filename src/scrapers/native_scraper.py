"""
Module: src/scrapers/native_scraper.py
Purpose: Built-in HTTP scraper using httpx and BeautifulSoup
Author: ScrapeSignal Team
Created: 2026-06-05

Dependencies:
    - httpx (async HTTP)
    - beautifulsoup4 (link discovery and extraction)

Used by:
    - src.scrapers.chain_scraper
"""

# Standard library
import logging
import re
from urllib.parse import urljoin, urlparse

# Third-party
import httpx
from bs4 import BeautifulSoup

# Local
from src.config import settings
from src.db.models import SourceConfig
from src.processors.extractor import Extractor
from src.scrapers.base import BaseScraper, ScrapedArticle
from src.utils.retry import async_retry

logger = logging.getLogger(__name__)

ARTICLE_PATH_HINTS = (
    "/news/",
    "/article/",
    "/articles/",
    "/blog/",
    "/story/",
    "/stories/",
    "/post/",
    "/posts/",
    "/press/",
    "/insights/",
    "/topic/",
)
YEAR_IN_PATH = re.compile(r"/20\d{2}/")
SKIP_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".pdf", ".zip", ".css", ".js")


class NativeScraper(BaseScraper):
    """Scrape article pages directly without third-party scraping APIs."""

    def __init__(self) -> None:
        """Initialize scraper dependencies."""
        self.extractor = Extractor()

    async def scrape(self, source: SourceConfig) -> list[ScrapedArticle]:
        """Scrape a source by discovering and fetching article pages.

        Args:
            source: Source configuration.

        Returns:
            Normalized article candidates.
        """
        homepage_html = await self._fetch_text(source.url)
        article_urls = self._discover_article_urls(source.url, homepage_html)
        if not article_urls:
            candidate = self.extractor.from_html(homepage_html, source.url)
            candidate["raw_metadata"] = {"provider": "native", "mode": "homepage"}
            return [candidate]  # type: ignore[list-item]

        limit = min(
            source.max_articles,
            settings.NATIVE_MAX_ARTICLE_PAGES,
        )
        candidates: list[ScrapedArticle] = []
        for url in article_urls[:limit]:
            try:
                html = await self._fetch_text(url)
                article = self.extractor.from_html(html, url)
                body = str(article.get("body") or "")
                if len(body.split()) < 40:
                    continue
                article["raw_metadata"] = {"provider": "native", "mode": "article"}
                candidates.append(article)  # type: ignore[arg-type]
            except Exception as error:
                logger.warning("Native article fetch failed for %s: %s", url, error)
        return candidates

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def _fetch_text(self, url: str) -> str:
        """Fetch page HTML.

        Args:
            url: Page URL.

        Returns:
            Response body text.
        """
        async with httpx.AsyncClient(
            timeout=self._timeout(),
            headers={"User-Agent": settings.USER_AGENT},
            follow_redirects=True,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def _discover_article_urls(self, base_url: str, html: str) -> list[str]:
        """Discover likely article URLs on a listing or homepage.

        Args:
            base_url: Source base URL.
            html: Homepage HTML.

        Returns:
            Candidate article URLs ordered by relevance heuristics.
        """
        soup = BeautifulSoup(html, "html.parser")
        base = urlparse(base_url)
        scored: list[tuple[int, str]] = []
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = str(anchor["href"]).strip()
            if not href or href.startswith(("#", "mailto:", "javascript:")):
                continue
            absolute = urljoin(base_url, href)
            parsed = urlparse(absolute)
            if parsed.scheme not in {"http", "https"}:
                continue
            if parsed.netloc and parsed.netloc != base.netloc:
                continue
            normalized = absolute.split("#", maxsplit=1)[0].rstrip("/")
            lower = normalized.lower()
            if any(lower.endswith(ext) for ext in SKIP_EXTENSIONS):
                continue
            if normalized in seen or normalized == base_url.rstrip("/"):
                continue
            score = self._score_article_url(normalized)
            if score <= 0:
                continue
            seen.add(normalized)
            scored.append((score, normalized))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [url for _, url in scored]

    def _score_article_url(self, url: str) -> int:
        """Score a URL for article-likelihood.

        Args:
            url: Candidate URL.

        Returns:
            Score where higher means more likely to be an article page.
        """
        lower = url.lower()
        score = 0
        if any(hint in lower for hint in ARTICLE_PATH_HINTS):
            score += 5
        if YEAR_IN_PATH.search(lower):
            score += 3
        path = urlparse(url).path
        segments = [segment for segment in path.split("/") if segment]
        if len(segments) >= 2:
            score += 1
        if len(path) > 20:
            score += 1
        return score

    def _timeout(self) -> httpx.Timeout:
        """Build HTTP timeout.

        Returns:
            Configured timeout.
        """
        return httpx.Timeout(
            settings.SCRAPE_TIMEOUT_SECONDS,
            connect=settings.SCRAPE_CONNECT_TIMEOUT_SECONDS,
        )
