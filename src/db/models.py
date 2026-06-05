"""
Module: src/db/models.py
Purpose: SQLAlchemy 2.0 ORM models for ScrapeSignal persistence
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - sqlalchemy.orm (declarative mapping)

Used by:
    - src.processors.* (article processing)
    - src.scrapers.manager (article persistence)
    - src.email.generator (email content)
    - src.main (orchestration)
"""

# Standard library
from datetime import UTC, datetime
from typing import Any

# Third-party
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    """Return timezone-aware UTC timestamp.

    Returns:
        Current UTC datetime.
    """
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class Article(Base):
    """Article scraped from a configured source."""

    __tablename__ = "articles"
    __table_args__ = (
        Index("idx_articles_score_sent", "relevance_score", "email_sent_date"),
        Index("idx_articles_source_published", "source_key", "published_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_key: Mapped[str] = mapped_column(String(100), index=True)
    source_name: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(2048), unique=True, index=True)
    canonical_url: Mapped[str | None] = mapped_column(String(2048), index=True)
    body: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(2048))
    author: Mapped[str | None] = mapped_column(String(300))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email_sent_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    def __repr__(self) -> str:
        """Return readable article representation.

        Returns:
            Debug-friendly representation.
        """
        return (
            f"<Article(id={self.id}, title='{self.title[:40]}...', "
            f"score={self.relevance_score})>"
        )


class DedupHash(Base):
    """Content hash used to prevent duplicate article delivery."""

    __tablename__ = "dedup_hashes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    article_id: Mapped[int | None] = mapped_column(ForeignKey("articles.id"))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class SourceConfig(Base):
    """Configured source for daily scraping."""

    __tablename__ = "source_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(2048))
    scraper_type: Mapped[str] = mapped_column(String(50), default="firecrawl")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    max_articles: Mapped[int] = mapped_column(Integer, default=150)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    scrape_logs: Mapped[list["ScrapeLog"]] = relationship(back_populates="source")


class KeywordMaster(Base):
    """Keyword and weight configuration for relevance scoring."""

    __tablename__ = "keywords_master"
    __table_args__ = (UniqueConstraint("keyword", "tier", name="uq_keyword_tier"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword: Mapped[str] = mapped_column(String(200), index=True)
    tier: Mapped[int] = mapped_column(Integer, index=True)
    weight: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(100), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )


class ScrapeLog(Base):
    """Execution log for source-level scraping."""

    __tablename__ = "scrape_logs"
    __table_args__ = (Index("idx_scrape_logs_run_status", "run_id", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(100), index=True)
    source_config_id: Mapped[int | None] = mapped_column(
        ForeignKey("source_configs.id")
    )
    status: Mapped[str] = mapped_column(String(50), index=True)
    articles_found: Mapped[int] = mapped_column(Integer, default=0)
    articles_saved: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float | None] = mapped_column(Float)

    source: Mapped[SourceConfig | None] = relationship(back_populates="scrape_logs")


class EmailLog(Base):
    """Delivery log for daily email briefs."""

    __tablename__ = "email_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(100), index=True)
    recipient_email: Mapped[str] = mapped_column(String(320), index=True)
    subject: Mapped[str] = mapped_column(String(500))
    article_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), index=True)
    sendgrid_message_id: Mapped[str | None] = mapped_column(String(200))
    error_message: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
