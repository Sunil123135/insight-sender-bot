"""
Module: tests/test_config.py
Purpose: Unit tests for ScrapeSignal settings contract
Author: ScrapeSignal Team
Created: 2026-05-10
"""

# Local
from src.config import settings


def test_core_contract_constants() -> None:
    """Core delivery constants match specification."""
    assert settings.RECIPIENT_EMAIL == "sunil.lalwani@quidelortho.com"
    assert settings.CRON_SCHEDULE == "30 1 * * *"
    assert settings.ARTICLES_PER_EMAIL == 20
    assert settings.MIN_RELEVANCE_SCORE == 70.0
