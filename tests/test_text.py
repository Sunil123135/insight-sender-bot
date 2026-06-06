"""Unit tests for text utilities."""

from src.utils.text import sanitize_postgres_text


def test_sanitize_postgres_text_removes_nul_bytes() -> None:
    """NUL bytes are stripped before PostgreSQL persistence."""
    assert sanitize_postgres_text("hello\x00world") == "helloworld"
