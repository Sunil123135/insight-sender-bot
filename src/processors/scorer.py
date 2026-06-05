"""
Module: src/processors/scorer.py
Purpose: Score articles for relevance to supply chain and AI topics
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.config.py (settings)
    - src.db.models.py (KeywordMaster)

Used by:
    - src.scrapers.manager (post-extraction scoring)
    - src.main (orchestrator)
"""

# Standard library
import logging
import re

# Local
from src.config import settings
from src.db.models import KeywordMaster

logger = logging.getLogger(__name__)

SOURCE_AUTHORITY_BOOSTS: dict[str, float] = {
    "arxiv": 10.0,
    "mit": 8.0,
    "supplychaindive": 6.0,
    "supplychainbrain": 6.0,
    "scmr": 5.0,
}
TITLE_MULTIPLIER = 1.8
MAX_SCORE = 100.0


class RelevanceScorer:
    """Score article relevance using a four-tier keyword system."""

    DEFAULT_KEYWORDS: dict[str, tuple[int, float]] = {
        "supply chain artificial intelligence": (1, 35.0),
        "ai supply chain": (1, 35.0),
        "pharmaceutical supply chain": (1, 35.0),
        "cold chain": (1, 30.0),
        "supply chain": (2, 18.0),
        "logistics": (2, 16.0),
        "inventory management": (2, 16.0),
        "artificial intelligence": (2, 18.0),
        "machine learning": (2, 17.0),
        "generative ai": (2, 18.0),
        "demand forecasting": (2, 18.0),
        "disruption": (3, 10.0),
        "resilience": (3, 9.0),
        "supplier": (3, 8.0),
        "manufacturing": (3, 8.0),
        "automation": (4, 5.0),
        "freight": (4, 5.0),
        "quality": (4, 4.0),
    }

    def __init__(self, keywords: list[KeywordMaster] | None = None) -> None:
        """Initialize scorer.

        Args:
            keywords: Optional keyword rows loaded from database.
        """
        self.keyword_weights: dict[str, float] = self._load_keywords(keywords)

    def _load_keywords(self, keywords: list[KeywordMaster] | None) -> dict[str, float]:
        """Load keyword weights from DB rows or defaults.

        Args:
            keywords: Optional keyword rows.

        Returns:
            Mapping of keyword to weight.
        """
        if not keywords:
            return {
                keyword: weight
                for keyword, (_, weight) in self.DEFAULT_KEYWORDS.items()
            }
        return {row.keyword.lower(): row.weight for row in keywords if row.enabled}

    def score(
        self, title: str | None, body: str | None, source: str | None = None
    ) -> float:
        """Score article relevance to supply chain and AI topics.

        Args:
            title: Article headline.
            body: Article body text.
            source: Source key or domain.

        Returns:
            Relevance score between 0.0 and 100.0.
        """
        normalized_title = self._normalize(title)
        normalized_body = self._normalize(body)[:20_000]
        if not normalized_title and not normalized_body:
            return 0.0

        score = 0.0
        for keyword, weight in self.keyword_weights.items():
            pattern = self._keyword_pattern(keyword)
            if re.search(pattern, normalized_title):
                score += weight * TITLE_MULTIPLIER
            if re.search(pattern, normalized_body):
                score += weight

        score += self._authority_boost(source)
        final_score = min(MAX_SCORE, round(score, 2))
        logger.debug(
            "Scored article title=%r source=%r score=%s", title, source, final_score
        )
        return (
            final_score if final_score >= settings.MIN_RELEVANCE_SCORE else final_score
        )

    def _authority_boost(self, source: str | None) -> float:
        """Return authority boost for trusted sources.

        Args:
            source: Source key or domain.

        Returns:
            Boost score.
        """
        if not source:
            return 0.0
        lowered = source.lower()
        for key, boost in SOURCE_AUTHORITY_BOOSTS.items():
            if key in lowered:
                return boost
        return 0.0

    def _keyword_pattern(self, keyword: str) -> str:
        """Build word-boundary regex for a keyword.

        Args:
            keyword: Keyword phrase.

        Returns:
            Regex pattern string.
        """
        escaped = re.escape(keyword.lower()).replace(r"\ ", r"\s+")
        return rf"\b{escaped}\b"

    def _normalize(self, value: str | None) -> str:
        """Normalize text for scoring.

        Args:
            value: Raw text.

        Returns:
            Lowercase normalized string.
        """
        if not value:
            return ""
        return re.sub(r"\s+", " ", value.lower()).strip()
