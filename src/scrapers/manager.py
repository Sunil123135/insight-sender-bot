"""
Module: src/scrapers/manager.py
Purpose: Orchestrate source scraping, extraction, scoring, dedupe, and persistence
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.scrapers.* (source adapters)
    - src.processors.* (dedupe/scoring)
    - src.db.repository (persistence)

Used by:
    - src.main (orchestrator)
"""

# Standard library
import asyncio
import logging
from datetime import UTC, datetime
from typing import cast

# Third-party
from sqlalchemy.ext.asyncio import AsyncSession

# Local
from src.db.models import Article, ScrapeLog, SourceConfig
from src.db.repository import remember_hashes, upsert_articles
from src.processors.deduplicator import ArticleCandidate, Deduplicator
from src.processors.scorer import RelevanceScorer
from src.scrapers.apify_scraper import ApifyScraper
from src.scrapers.arxiv_scraper import ArxivScraper
from src.scrapers.base import BaseScraper, ScrapedArticle
from src.scrapers.firecrawl_scraper import FirecrawlScraper
from src.scrapers.jina_scraper import JinaScraper

logger = logging.getLogger(__name__)


class ScraperManager:
    """Coordinate all configured source scrapers."""

    def __init__(self, scorer: RelevanceScorer | None = None) -> None:
        """Initialize manager dependencies.

        Args:
            scorer: Optional scorer instance.
        """
        self.scorer = scorer or RelevanceScorer()
        self.deduplicator = Deduplicator()
        self.scrapers: dict[str, BaseScraper] = {
            "firecrawl": FirecrawlScraper(),
            "jina": JinaScraper(),
            "apify": ApifyScraper(),
            "arxiv": ArxivScraper(),
        }

    async def scrape_all(
        self,
        session: AsyncSession,
        sources: list[SourceConfig],
        run_id: str,
    ) -> list[Article]:
        """Scrape all sources concurrently and persist articles.

        Args:
            session: Active database session.
            sources: Enabled sources.
            run_id: Current run identifier.

        Returns:
            Candidate Article objects.
        """
        logger.info("Scraping %s sources", len(sources))
        tasks = [self._scrape_source(source, run_id) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        articles: list[Article] = []
        logs: list[ScrapeLog] = []
        for source, result in zip(sources, results, strict=True):
            if isinstance(result, Exception):
                logger.error(
                    "Source failed source=%s error=%s",
                    source.source_key,
                    result,
                    exc_info=True,
                )
            elif isinstance(result, tuple):
                log, scraped = result
                logs.append(log)
                articles.extend(scraped)
        for log in logs:
            session.add(log)
        unique = self._dedupe_articles(articles)
        saved = await upsert_articles(session, unique)
        await remember_hashes(session, [article.content_hash for article in unique])
        logger.info(
            "ScraperManager produced %s unique articles, saved=%s", len(unique), saved
        )
        return unique

    async def _scrape_source(
        self,
        source: SourceConfig,
        run_id: str,
    ) -> tuple[ScrapeLog, list[Article]]:
        """Scrape one source without holding a database transaction.

        Args:
            source: Source configuration.
            run_id: Current run identifier.

        Returns:
            Scrape log and scored Article instances.
        """
        started = datetime.now(UTC)
        log = ScrapeLog(
            run_id=run_id,
            source_config_id=source.id,
            status="running",
            started_at=started,
        )
        scraper = self.scrapers.get(source.scraper_type, self.scrapers["firecrawl"])
        try:
            candidates = await scraper.scrape(source)
            articles = [self._to_article(source, candidate) for candidate in candidates]
            log.status = "success"
            log.articles_found = len(candidates)
            log.articles_saved = len(articles)
            return log, articles
        except Exception as error:
            log.status = "failed"
            log.error_message = str(error)
            logger.error("Scraping failed for %s", source.source_key, exc_info=True)
            return log, []
        finally:
            completed = datetime.now(UTC)
            log.completed_at = completed
            log.duration_seconds = (completed - started).total_seconds()

    def _to_article(self, source: SourceConfig, candidate: ScrapedArticle) -> Article:
        """Convert scraper candidate to ORM Article.

        Args:
            source: Source configuration.
            candidate: Scraped candidate.

        Returns:
            Article ORM instance.
        """
        typed = cast(ArticleCandidate, dict(candidate))
        content_hash = typed.get("content_hash") or ""
        score = self.scorer.score(
            str(candidate.get("title") or ""),
            str(candidate.get("body") or ""),
            source.source_key,
        )
        return Article(
            source_key=source.source_key,
            source_name=source.name,
            title=str(candidate.get("title") or source.name)[:500],
            url=str(candidate.get("url") or source.url),
            canonical_url=candidate.get("canonical_url"),
            body=str(candidate.get("body") or ""),
            image_url=candidate.get("image_url"),
            author=candidate.get("author"),
            published_at=cast(datetime | None, candidate.get("published_at")),
            relevance_score=score,
            content_hash=content_hash,
            raw_metadata=cast(dict[str, object], candidate.get("raw_metadata") or {}),
        )

    def _dedupe_articles(self, articles: list[Article]) -> list[Article]:
        """Deduplicate and populate missing content hashes.

        Args:
            articles: Article objects.

        Returns:
            Unique article objects.
        """
        candidates: list[ArticleCandidate] = [
            {"title": article.title, "body": article.body, "url": article.url}
            for article in articles
        ]
        deduped = self.deduplicator.deduplicate(candidates)
        hashes = [candidate["content_hash"] for candidate in deduped]
        unique_articles: list[Article] = []
        for article, content_hash in zip(articles, hashes, strict=False):
            article.content_hash = content_hash
            unique_articles.append(article)
        return unique_articles
