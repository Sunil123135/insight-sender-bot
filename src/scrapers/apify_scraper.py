"""
Module: src/scrapers/apify_scraper.py
Purpose: Apify Website Content Crawler scraper for primary industry sources
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - httpx (async Apify API calls)
    - src.processors.extractor (direct HTML fallback)

Used by:
    - src.scrapers.manager

Apify API pattern (equivalent curl):

    echo '{"startUrls":[{"url":"https://example.com"}],"maxCrawlPages":10}' |
    curl -X POST -d @- \\
      -H 'Content-Type: application/json' \\
      -H 'Authorization: Bearer <YOUR_API_TOKEN>' \\
      -L 'https://api.apify.com/v2/acts/apify~website-content-crawler/run-sync-get-dataset-items?clean=true'
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

APIFY_API_BASE = "https://api.apify.com/v2"


class ApifyScraper(BaseScraper):
    """Scrape websites using an Apify actor via run-sync-get-dataset-items."""

    def __init__(self) -> None:
        """Initialize scraper dependencies."""
        self.extractor = Extractor()

    async def scrape(self, source: SourceConfig) -> list[ScrapedArticle]:
        """Scrape a source through Apify.

        Args:
            source: Source configuration.

        Returns:
            Normalized article candidates.
        """
        if not settings.secret_is_set(settings.APIFY_API_TOKEN):
            logger.warning(
                "APIFY_API_TOKEN missing; using direct fallback for %s",
                source.source_key,
            )
            return await self._direct_fallback(source)

        task_id = self._task_id(source)
        if task_id:
            rows = await self._fetch_task_dataset(task_id)
        else:
            rows = await self._run_actor_sync(source)

        return [self._normalize(row, source) for row in rows[: source.max_articles]]

    def _auth_headers(self) -> dict[str, str]:
        """Build Apify Bearer auth headers.

        Returns:
            Request headers for Apify API calls.
        """
        return {
            "Authorization": f"Bearer {settings.APIFY_API_TOKEN.get_secret_value()}",
            "Content-Type": "application/json",
        }

    def _task_id(self, source: SourceConfig) -> str | None:
        """Return optional legacy Apify actor task id from source metadata.

        Args:
            source: Source configuration.

        Returns:
            Task id when configured, otherwise None.
        """
        metadata = getattr(source, "raw_metadata", None)
        if not isinstance(metadata, dict):
            return None
        task_id = metadata.get("apify_task_id")
        return str(task_id) if task_id else None

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def _fetch_task_dataset(self, task_id: str) -> list[dict[str, object]]:
        """Fetch items from a preconfigured Apify actor task dataset.

        Args:
            task_id: Apify actor task id.

        Returns:
            Dataset rows.
        """
        url = f"{APIFY_API_BASE}/actor-tasks/{task_id}/runs/last/dataset/items"
        params = {"clean": "true"}
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                params=params,
                headers=self._auth_headers(),
            )
            response.raise_for_status()
            rows = response.json()
        return self._as_row_list(rows)

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def _run_actor_sync(self, source: SourceConfig) -> list[dict[str, object]]:
        """Run an Apify actor synchronously and return dataset items.

        Uses the same endpoint as Apify's documented curl example:
        POST /v2/acts/{actorId}/run-sync-get-dataset-items

        Args:
            source: Source configuration.

        Returns:
            Dataset rows from the actor run.
        """
        actor_id = settings.APIFY_ACTOR_ID
        url = f"{APIFY_API_BASE}/acts/{actor_id}/run-sync-get-dataset-items"
        payload = {
            "startUrls": [{"url": source.url}],
            "maxCrawlPages": min(source.max_articles, settings.MAX_ARTICLES_PER_SOURCE),
            "maxCrawlDepth": 2,
        }
        params = {
            "clean": "true",
            "timeout": int(settings.APIFY_RUN_TIMEOUT_SECONDS),
        }
        timeout = httpx.Timeout(
            settings.APIFY_RUN_TIMEOUT_SECONDS + 30.0,
            connect=settings.SCRAPE_CONNECT_TIMEOUT_SECONDS,
        )
        logger.info(
            "Running Apify actor %s synchronously for %s",
            actor_id,
            source.source_key,
        )
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.post(
                url,
                params=params,
                json=payload,
                headers=self._auth_headers(),
            )
            response.raise_for_status()
            rows = response.json()
        return self._as_row_list(rows)

    def _as_row_list(self, rows: object) -> list[dict[str, object]]:
        """Coerce Apify dataset response into a list of dict rows.

        Args:
            rows: Raw JSON response.

        Returns:
            Dataset rows.
        """
        if not isinstance(rows, list):
            return []
        return [row for row in rows if isinstance(row, dict)]

    async def _direct_fallback(self, source: SourceConfig) -> list[ScrapedArticle]:
        """Fetch homepage directly when Apify credentials are absent.

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
        metadata = row.get("metadata")
        meta = metadata if isinstance(metadata, dict) else {}
        title = row.get("title") or meta.get("title") or source.name
        body = row.get("text") or row.get("markdown") or meta.get("description") or ""
        url = row.get("url") or row.get("loadedUrl") or source.url
        return {
            "title": str(title),
            "url": str(url),
            "canonical_url": str(url),
            "body": str(body),
            "image_url": str(row.get("imageUrl") or meta.get("imageUrl") or "") or None,
            "author": str(row.get("author") or meta.get("author") or "") or None,
            "published_at": None,
            "raw_metadata": {"provider": "apify", "item": row},
        }

    def _timeout(self) -> httpx.Timeout:
        """Build HTTP timeout.

        Returns:
            Configured timeout.
        """
        return httpx.Timeout(
            settings.SCRAPE_TIMEOUT_SECONDS,
            connect=settings.SCRAPE_CONNECT_TIMEOUT_SECONDS,
        )
