"""
Module: tests/test_scorer.py
Purpose: Unit tests for ScrapeSignal relevance scoring
Author: ScrapeSignal Team
Created: 2026-05-10
"""

# Third-party
import pytest

# Local
from src.processors.scorer import RelevanceScorer


class TestRelevanceScorer:
    """Test suite for RelevanceScorer."""

    @pytest.fixture
    def scorer(self) -> RelevanceScorer:
        """Provide a fresh scorer instance."""
        return RelevanceScorer()

    def test_high_relevance_supply_chain_article(self, scorer: RelevanceScorer) -> None:
        """Supply chain and AI article scores high."""
        score = scorer.score(
            "AI Revolutionizes Supply Chain Logistics",
            "Machine learning improves warehouse automation and inventory management.",
        )
        assert score >= 90.0

    def test_low_relevance_article_scores_zero(self, scorer: RelevanceScorer) -> None:
        """Unrelated article scores low."""
        assert scorer.score("Travel Tips", "Vacation ideas") == 0.0

    def test_empty_inputs_return_zero(self, scorer: RelevanceScorer) -> None:
        """Empty inputs produce zero score."""
        assert scorer.score("", "") == 0.0

    def test_arxiv_source_boost(self, scorer: RelevanceScorer) -> None:
        """Trusted source increases score."""
        base_score = scorer.score("AI research", "machine learning")
        boosted_score = scorer.score(
            "AI research", "machine learning", source="arxiv.org"
        )
        assert boosted_score > base_score

    @pytest.mark.parametrize(
        ("title", "minimum"),
        [
            ("Supply chain disruption", 40.0),
            ("Cold chain pharmaceutical supply chain", 90.0),
            ("AI supply chain logistics", 90.0),
        ],
    )
    def test_various_topics(
        self, scorer: RelevanceScorer, title: str, minimum: float
    ) -> None:
        """Relevant topics score above expected minimum."""
        assert scorer.score(title, "") >= minimum
