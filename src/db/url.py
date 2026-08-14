"""
Module: src/db/url.py
Purpose: Normalize PostgreSQL connection URLs for async SQLAlchemy + Neon
Author: ScrapeSignal Team
Created: 2026-06-05

Dependencies:
    - urllib.parse

Used by:
    - src.db.session (engine creation)
    - alembic/env.py (migrations)
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_ASYNC_DRIVER_PREFIXES = (
    "postgresql+psycopg://",
    "postgresql+asyncpg://",
)


def normalize_database_url(
    database_url: str, *, connect_timeout_seconds: int = 30
) -> str:
    """Normalize configured PostgreSQL URL for SQLAlchemy async psycopg.

    Neon console strings often use ``postgresql://`` or ``ssl=require`` query
    keys. This helper converts them to the async psycopg driver with psycopg-
    compatible SSL options and a bounded connect timeout.

    Args:
        database_url: URL from settings or Neon console.
        connect_timeout_seconds: psycopg connect timeout in seconds.

    Returns:
        SQLAlchemy URL using the async psycopg driver.
    """
    normalized = database_url.strip()
    if normalized.startswith("postgresql://"):
        normalized = "postgresql+psycopg://" + normalized.removeprefix("postgresql://")
    if normalized.startswith("postgresql+asyncpg://"):
        normalized = "postgresql+psycopg://" + normalized.removeprefix(
            "postgresql+asyncpg://"
        )

    parsed = urlparse(normalized)
    query_pairs: list[tuple[str, str]] = []
    has_sslmode = False
    has_connect_timeout = False

    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key == "channel_binding":
            continue
        if key == "ssl":
            query_pairs.append(("sslmode", value))
            has_sslmode = True
            continue
        if key == "connect_timeout":
            has_connect_timeout = True
        query_pairs.append((key, value))
        if key == "sslmode":
            has_sslmode = True

    if not has_sslmode:
        host = (parsed.hostname or "").lower()
        # Local Docker/dev Postgres typically has no TLS; require SSL for remote hosts.
        if host in {"localhost", "127.0.0.1", "::1"}:
            query_pairs.append(("sslmode", "disable"))
        else:
            query_pairs.append(("sslmode", "require"))
    if not has_connect_timeout:
        query_pairs.append(("connect_timeout", str(connect_timeout_seconds)))

    return urlunparse(parsed._replace(query=urlencode(query_pairs)))


def is_async_database_url(database_url: str) -> bool:
    """Return whether the URL uses an async SQLAlchemy PostgreSQL driver.

    Args:
        database_url: Database URL from settings.

    Returns:
        True when the URL is async-driver compatible or plain ``postgresql://``.
    """
    return database_url.startswith(_ASYNC_DRIVER_PREFIXES + ("postgresql://",))
