"""
Module: tests/test_runtime.py
Purpose: Unit tests for logging, Slack alerts, and orchestration
Author: ScrapeSignal Team
Created: 2026-05-10
"""

# Standard library
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

# Third-party
import pytest

# Local
from src import main
from src.db.models import Article
from src.logger import setup_logging
from src.utils import slack_alerts


def test_setup_logging() -> None:
    """Logger setup installs handlers."""
    setup_logging()
    import logging

    assert logging.getLogger().handlers


@pytest.mark.asyncio
async def test_slack_alert_suppressed_without_webhook() -> None:
    """Missing webhook does not raise."""
    await slack_alerts.send_slack_alert("test", severity="critical")


class FakeSession:
    """Fake async session for orchestrator tests."""

    def __init__(self) -> None:
        """Initialize collected rows."""
        self.rows: list[object] = []

    def add(self, row: object) -> None:
        """Collect added row."""
        self.rows.append(row)


@asynccontextmanager
async def fake_get_db() -> AsyncIterator[FakeSession]:
    """Yield fake session."""
    yield FakeSession()


class FakeManager:
    """Fake scraper manager."""

    def __init__(self, scorer: object) -> None:
        """Accept scorer dependency."""
        self.scorer = scorer

    async def scrape_all(
        self,
        session: FakeSession,
        sources: list[object],
        run_id: str,
    ) -> list[Article]:
        """Return no newly scraped articles."""
        return []


class FakeSummarizer:
    """Fake summarizer."""

    async def summarize_articles(self, articles: list[Article]) -> list[Article]:
        """Populate summaries."""
        for article in articles:
            article.summary = "Summary"
        return articles


@pytest.mark.asyncio
async def test_orchestrator_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Orchestrator succeeds with mocked dependencies."""
    article = Article(
        source_key="s",
        source_name="S",
        title="AI supply chain",
        url="https://example.com",
        canonical_url="https://example.com",
        body="machine learning logistics",
        relevance_score=95,
        content_hash="d" * 64,
    )

    async def no_op_int(session: object) -> int:
        return 0

    async def sources(session: object) -> list[object]:
        return []

    async def keywords(session: object) -> list[object]:
        return []

    async def top_articles(session: object) -> list[Article]:
        return [article]

    async def mark(session: object, articles: list[Article], sent_at: datetime) -> None:
        assert sent_at.tzinfo == UTC

    monkeypatch.setattr(main, "get_db", fake_get_db)
    monkeypatch.setattr(main, "purge_expired_hashes", no_op_int)
    monkeypatch.setattr(main, "get_enabled_sources", sources)
    monkeypatch.setattr(main, "get_enabled_keywords", keywords)
    monkeypatch.setattr(main, "select_top_articles", top_articles)
    monkeypatch.setattr(main, "mark_articles_emailed", mark)
    monkeypatch.setattr(main, "ScraperManager", FakeManager)

    orchestrator = main.ScrapeSignalOrchestrator()
    orchestrator.summarizer = FakeSummarizer()  # type: ignore[assignment]
    assert await orchestrator.run() == 0
