"""
Module: tests/test_repository.py
Purpose: Unit tests for repository query helpers with fake async sessions
Author: ScrapeSignal Team
Created: 2026-05-10
"""

# Standard library
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

# Third-party
import pytest

# Local
from src.db import repository
from src.db.models import Article, KeywordMaster, SourceConfig


class FakeScalarResult:
    """Fake SQLAlchemy scalar result."""

    def __init__(self, rows: list[Any]) -> None:
        """Initialize fake rows."""
        self.rows = rows

    def all(self) -> list[Any]:
        """Return rows."""
        return self.rows


class FakeResult:
    """Fake SQLAlchemy result."""

    def __init__(self, rows: list[Any] | None = None, rowcount: int = 0) -> None:
        """Initialize fake result."""
        self.rows = rows or []
        self.rowcount = rowcount

    def scalars(self) -> FakeScalarResult:
        """Return fake scalar result."""
        return FakeScalarResult(self.rows)


@dataclass
class FakeSession:
    """Fake async session with deterministic result."""

    result: FakeResult

    async def execute(self, statement: object) -> FakeResult:
        """Return configured result."""
        return self.result


@pytest.mark.asyncio
async def test_get_enabled_sources() -> None:
    """Repository loads source rows."""
    source = SourceConfig(source_key="s", name="S", url="https://example.com")
    session = FakeSession(FakeResult([source]))
    assert await repository.get_enabled_sources(session) == [source]  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_get_enabled_keywords() -> None:
    """Repository loads keyword rows."""
    keyword = KeywordMaster(keyword="ai", tier=1, weight=10, category="ai")
    session = FakeSession(FakeResult([keyword]))
    assert await repository.get_enabled_keywords(session) == [keyword]  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_upsert_articles_empty() -> None:
    """Empty upsert returns zero."""
    session = FakeSession(FakeResult(rowcount=1))
    assert await repository.upsert_articles(session, []) == 0  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_upsert_articles_non_empty() -> None:
    """Upsert reports rowcount for article inserts."""
    article = Article(
        source_key="s",
        source_name="S",
        title="T",
        url="https://example.com/insert",
        canonical_url="https://example.com/insert",
        body="B",
        relevance_score=90,
        content_hash="e" * 64,
    )
    session = FakeSession(FakeResult(rowcount=1))
    assert await repository.upsert_articles(session, [article]) == 1  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_remember_hashes_and_purge() -> None:
    """Hash helpers return rowcounts."""
    session = FakeSession(FakeResult(rowcount=2))
    assert await repository.remember_hashes(session, ["f" * 64, "g" * 64]) == 2  # type: ignore[arg-type]
    assert await repository.purge_expired_hashes(session) == 2  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_remember_hashes_empty() -> None:
    """No hashes returns zero."""
    session = FakeSession(FakeResult(rowcount=2))
    assert await repository.remember_hashes(session, []) == 0  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_mark_articles_emailed() -> None:
    """Article email timestamp is assigned."""
    article = Article(
        source_key="s",
        source_name="S",
        title="T",
        url="https://example.com/email",
        canonical_url="https://example.com/email",
        body="B",
        relevance_score=90,
        content_hash="h" * 64,
    )
    sent_at = datetime.now(UTC)
    await repository.mark_articles_emailed(  # type: ignore[arg-type]
        FakeSession(FakeResult()),
        [article],
        sent_at,
    )
    assert article.email_sent_date == sent_at


@pytest.mark.asyncio
async def test_select_top_articles() -> None:
    """Repository returns selected articles."""
    article = Article(
        source_key="s",
        source_name="S",
        title="T",
        url="https://example.com",
        canonical_url="https://example.com",
        body="B",
        relevance_score=90,
        content_hash="c" * 64,
    )
    session = FakeSession(FakeResult([article]))
    assert await repository.select_top_articles(session) == [article]  # type: ignore[arg-type]
