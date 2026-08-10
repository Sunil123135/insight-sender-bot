"""
Module: tests/test_db_url.py
Purpose: Unit tests for PostgreSQL URL normalization
Author: ScrapeSignal Team
Created: 2026-06-05
"""

# Local
from src.db.url import normalize_database_url


def test_normalize_neon_asyncpg_url() -> None:
    """Neon asyncpg URLs are converted to psycopg with sslmode."""
    raw = (
        "postgresql+asyncpg://user:pass@ep-example-pooler.aws.neon.tech/neondb"
        "?ssl=require&channel_binding=require"
    )
    normalized = normalize_database_url(raw, connect_timeout_seconds=15)
    assert normalized.startswith("postgresql+psycopg://")
    assert "sslmode=require" in normalized
    assert "channel_binding" not in normalized
    assert "connect_timeout=15" in normalized


def test_normalize_plain_postgresql_url() -> None:
    """Plain postgresql:// URLs from Neon console are accepted."""
    raw = "postgresql://user:pass@ep-example.aws.neon.tech/neondb"
    normalized = normalize_database_url(raw)
    assert normalized.startswith("postgresql+psycopg://")
    assert "sslmode=require" in normalized


def test_normalize_local_postgresql_url_disables_ssl() -> None:
    """Local Postgres URLs default to sslmode=disable."""
    raw = "postgresql://user:pass@localhost:5432/scrapesignal"
    normalized = normalize_database_url(raw)
    assert normalized.startswith("postgresql+psycopg://")
    assert "sslmode=disable" in normalized
    assert "sslmode=require" not in normalized
