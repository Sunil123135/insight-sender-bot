"""
Module: src/db/repository.py
Purpose: Query helpers for ScrapeSignal database access
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.db.models (ORM models)
    - sqlalchemy (query construction)

Used by:
    - src.scrapers.manager (source loading and persistence)
    - src.email.generator (article selection)
    - src.main (orchestration)
"""

# Standard library
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

# Third-party
from sqlalchemy import Select, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

# Local
from src.config import settings
from src.db.models import Article, DedupHash, KeywordMaster, SourceConfig

logger = logging.getLogger(__name__)


async def get_enabled_sources(session: AsyncSession) -> list[SourceConfig]:
    """Load enabled source configurations.

    Args:
        session: Active async database session.

    Returns:
        Enabled sources ordered by priority.
    """
    result = await session.execute(
        select(SourceConfig)
        .where(SourceConfig.enabled.is_(True))
        .order_by(SourceConfig.priority.asc())
    )
    sources = list(result.scalars().all())
    logger.info("Loaded %s enabled sources", len(sources))
    return sources


async def get_enabled_keywords(session: AsyncSession) -> list[KeywordMaster]:
    """Load enabled keyword configuration.

    Args:
        session: Active async database session.

    Returns:
        Enabled keyword rows ordered by tier.
    """
    result = await session.execute(
        select(KeywordMaster)
        .where(KeywordMaster.enabled.is_(True))
        .order_by(KeywordMaster.tier.asc())
    )
    return list(result.scalars().all())


async def upsert_articles(session: AsyncSession, articles: list[Article]) -> int:
    """Insert articles while ignoring URL/content duplicates.

    Args:
        session: Active async database session.
        articles: Article ORM instances to persist.

    Returns:
        Number of inserted rows reported by PostgreSQL.
    """
    if not articles:
        return 0

    rows = [
        {
            column.name: getattr(article, column.name)
            for column in Article.__table__.columns
            if column.name != "id"
        }
        for article in articles
    ]
    statement = insert(Article).values(rows).on_conflict_do_nothing()
    result = cast(CursorResult[Any], await session.execute(statement))
    saved = int(result.rowcount or 0)
    logger.info("Saved %s/%s candidate articles", saved, len(articles))
    return saved


async def remember_hashes(session: AsyncSession, hashes: list[str]) -> int:
    """Store deduplication hashes with retention expiry.

    Args:
        session: Active async database session.
        hashes: SHA-256 hashes to remember.

    Returns:
        Number of inserted hashes.
    """
    if not hashes:
        return 0
    expires_at = datetime.now(UTC) + timedelta(
        days=settings.DEDUPLICATION_WINDOW_DAYS,
    )
    rows = [{"content_hash": value, "expires_at": expires_at} for value in hashes]
    statement = (
        insert(DedupHash)
        .values(rows)
        .on_conflict_do_nothing(
            index_elements=["content_hash"],
        )
    )
    result = cast(CursorResult[Any], await session.execute(statement))
    return int(result.rowcount or 0)


async def select_top_articles(
    session: AsyncSession,
    limit: int = settings.ARTICLES_PER_EMAIL,
) -> list[Article]:
    """Select highest relevance unsent articles for the daily brief.

    Args:
        session: Active async database session.
        limit: Maximum number of articles to return.

    Returns:
        Ordered list of article rows.
    """
    statement: Select[tuple[Article]] = (
        select(Article)
        .where(Article.relevance_score >= settings.MIN_RELEVANCE_SCORE)
        .where(Article.email_sent_date.is_(None))
        .order_by(
            Article.relevance_score.desc(), Article.published_at.desc().nullslast()
        )
        .limit(limit)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def mark_articles_emailed(
    session: AsyncSession,
    articles: list[Article],
    sent_at: datetime,
) -> None:
    """Mark selected articles as emailed.

    Args:
        session: Active async database session.
        articles: Articles that were included in an email.
        sent_at: UTC sent timestamp.
    """
    for article in articles:
        article.email_sent_date = sent_at


async def purge_expired_hashes(session: AsyncSession) -> int:
    """Remove expired deduplication hashes.

    Args:
        session: Active async database session.

    Returns:
        Number of deleted rows.
    """
    result = cast(
        CursorResult[Any],
        await session.execute(
            delete(DedupHash).where(DedupHash.expires_at < datetime.now(UTC)),
        ),
    )
    return int(result.rowcount or 0)
