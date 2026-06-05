"""
Module: src/utils/hashing.py
Purpose: Generate stable SHA-256 content hashes for article deduplication
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - hashlib (SHA-256)

Used by:
    - src.processors.deduplicator
    - src.scrapers.manager
"""

# Standard library
import hashlib
import re

WHITESPACE_RE = re.compile(r"\s+")


def normalize_content(value: str | None) -> str:
    """Normalize article text before hashing.

    Args:
        value: Raw title or body value.

    Returns:
        Lowercase whitespace-normalized text.
    """
    if not value:
        return ""
    return WHITESPACE_RE.sub(" ", value.strip().lower())


def generate_content_hash(
    title: str | None, body: str | None, url: str | None = None
) -> str:
    """Generate a stable SHA-256 hash for article content.

    Args:
        title: Article title.
        body: Article body.
        url: Optional fallback URL when body is sparse.

    Returns:
        Hex SHA-256 digest.
    """
    normalized = "|".join(
        [
            normalize_content(title),
            normalize_content(body)[:10_000],
            normalize_content(url),
        ],
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
