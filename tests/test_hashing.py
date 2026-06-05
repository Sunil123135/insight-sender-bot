"""
Module: tests/test_hashing.py
Purpose: Unit tests for content hashing
Author: ScrapeSignal Team
Created: 2026-05-10
"""

# Local
from src.utils.hashing import generate_content_hash


def test_same_content_hashes_same() -> None:
    """Identical content produces identical hashes."""
    assert generate_content_hash("Title", "Body") == generate_content_hash(
        " title ", " body "
    )


def test_different_content_hashes_differently() -> None:
    """Different content produces different hashes."""
    assert generate_content_hash("Title 1", "Body") != generate_content_hash(
        "Title 2", "Body"
    )
