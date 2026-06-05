"""
Module: src/processors/deduplicator.py
Purpose: Deduplicate scraped articles using stable content hashes
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.utils.hashing (generate_content_hash)

Used by:
    - src.scrapers.manager
"""

# Standard library
import logging
from typing import TypedDict

# Local
from src.utils.hashing import generate_content_hash

logger = logging.getLogger(__name__)


class ArticleCandidate(TypedDict, total=False):
    """Raw extracted article candidate."""

    title: str
    url: str
    body: str
    content_hash: str


class Deduplicator:
    """Deduplicate article candidates within a single run."""

    def __init__(self) -> None:
        """Initialize an empty in-memory hash set."""
        self.seen_hashes: set[str] = set()

    def deduplicate(self, articles: list[ArticleCandidate]) -> list[ArticleCandidate]:
        """Remove duplicates from an article candidate list.

        Args:
            articles: Raw article dictionaries.

        Returns:
            Deduplicated article dictionaries with content_hash populated.
        """
        unique: list[ArticleCandidate] = []
        for article in articles:
            content_hash = generate_content_hash(
                article.get("title"),
                article.get("body"),
                article.get("url"),
            )
            if content_hash in self.seen_hashes:
                logger.info(
                    "Skipping duplicate candidate: %s", article.get("url", "unknown")
                )
                continue
            self.seen_hashes.add(content_hash)
            article["content_hash"] = content_hash
            unique.append(article)
        logger.info("Deduplicated %s candidates to %s", len(articles), len(unique))
        return unique
