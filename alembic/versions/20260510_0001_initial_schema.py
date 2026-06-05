"""
Module: alembic/versions/20260510_0001_initial_schema.py
Purpose: Initial ScrapeSignal schema migration
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - alembic
    - sqlalchemy

Used by:
    - alembic upgrade head
"""

# Third-party
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260510_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_key", sa.String(length=100), nullable=False),
        sa.Column("source_name", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("canonical_url", sa.String(length=2048), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("author", sa.String(length=300), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("email_sent_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "raw_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
    )
    op.create_index("ix_articles_url", "articles", ["url"], unique=True)
    op.create_index(
        "ix_articles_content_hash", "articles", ["content_hash"], unique=True
    )
    op.create_index("ix_articles_relevance_score", "articles", ["relevance_score"])
    op.create_index("ix_articles_email_sent_date", "articles", ["email_sent_date"])
    op.create_index(
        "idx_articles_score_sent", "articles", ["relevance_score", "email_sent_date"]
    )
    op.create_index(
        "idx_articles_source_published", "articles", ["source_key", "published_at"]
    )

    op.create_table(
        "source_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("scraper_type", sa.String(length=50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("max_articles", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_source_configs_source_key", "source_configs", ["source_key"], unique=True
    )
    op.create_index("ix_source_configs_enabled", "source_configs", ["enabled"])

    op.create_table(
        "keywords_master",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("keyword", sa.String(length=200), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("keyword", "tier", name="uq_keyword_tier"),
    )
    op.create_index("ix_keywords_master_keyword", "keywords_master", ["keyword"])
    op.create_index("ix_keywords_master_tier", "keywords_master", ["tier"])
    op.create_index("ix_keywords_master_category", "keywords_master", ["category"])

    op.create_table(
        "dedup_hashes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "article_id", sa.Integer(), sa.ForeignKey("articles.id"), nullable=True
        ),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_dedup_hashes_content_hash", "dedup_hashes", ["content_hash"], unique=True
    )
    op.create_index("ix_dedup_hashes_expires_at", "dedup_hashes", ["expires_at"])

    op.create_table(
        "scrape_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column(
            "source_config_id",
            sa.Integer(),
            sa.ForeignKey("source_configs.id"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("articles_found", sa.Integer(), nullable=False),
        sa.Column("articles_saved", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
    )
    op.create_index("ix_scrape_logs_run_id", "scrape_logs", ["run_id"])
    op.create_index("ix_scrape_logs_status", "scrape_logs", ["status"])
    op.create_index("idx_scrape_logs_run_status", "scrape_logs", ["run_id", "status"])

    op.create_table(
        "email_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("recipient_email", sa.String(length=320), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("article_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("sendgrid_message_id", sa.String(length=200), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_email_logs_run_id", "email_logs", ["run_id"])
    op.create_index("ix_email_logs_recipient_email", "email_logs", ["recipient_email"])
    op.create_index("ix_email_logs_status", "email_logs", ["status"])
    op.create_index("ix_email_logs_sent_at", "email_logs", ["sent_at"])


def downgrade() -> None:
    """Drop initial tables."""
    op.drop_table("email_logs")
    op.drop_table("scrape_logs")
    op.drop_table("dedup_hashes")
    op.drop_table("keywords_master")
    op.drop_table("source_configs")
    op.drop_table("articles")
