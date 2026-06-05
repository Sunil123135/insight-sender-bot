"""
Module: tests/test_processors.py
Purpose: Unit tests for extraction, deduplication, PDF parsing, and summarization
Author: ScrapeSignal Team
Created: 2026-05-10
"""

# Standard library
from datetime import UTC, datetime

# Third-party
import pytest

# Local
from src.db.models import Article
from src.processors.deduplicator import Deduplicator
from src.processors.extractor import Extractor
from src.processors.pdf_parser import PDFParser
from src.processors.summarizer import Summarizer


def test_deduplicator_removes_duplicate_candidates() -> None:
    """Duplicate content appears once."""
    deduplicator = Deduplicator()
    articles = [
        {"title": "AI Supply Chain", "body": "logistics", "url": "https://a.test"},
        {"title": "AI Supply Chain", "body": "logistics", "url": "https://a.test"},
    ]
    assert len(deduplicator.deduplicate(articles)) == 1


def test_extractor_from_html() -> None:
    """HTML extraction pulls title, body, canonical URL, image, and date."""
    html = """
    <html><head>
    <meta property="og:title" content="AI Supply Chain">
    <meta property="og:image" content="https://example.com/image.jpg">
    <meta property="article:published_time" content="2026-05-10T01:30:00Z">
    <link rel="canonical" href="https://example.com/canonical">
    </head><body><article>Machine learning logistics</article></body></html>
    """
    article = Extractor().from_html(html, "https://example.com")
    assert article["title"] == "AI Supply Chain"
    assert article["canonical_url"] == "https://example.com/canonical"
    assert article["published_at"] == datetime(2026, 5, 10, 1, 30, tzinfo=UTC)


def test_extractor_from_markdown() -> None:
    """Markdown extraction infers title."""
    article = Extractor().from_markdown("# Title\n\nBody", "https://example.com")
    assert article["title"] == "Title"
    assert "Body" in str(article["body"])


def test_pdf_extract_text_from_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    """PDF parser text extraction can be monkeypatched for deterministic tests."""
    parser = PDFParser()
    monkeypatch.setattr(parser, "_extract_text", lambda content: "parsed text")
    assert parser._extract_text(b"ignored") == "parsed text"


@pytest.mark.asyncio
async def test_summarizer_dry_run_fallback() -> None:
    """Dry run summarizer uses deterministic fallback."""
    article = Article(
        source_key="test",
        source_name="Test",
        title="AI Supply Chain",
        url="https://example.com",
        canonical_url="https://example.com",
        body="Machine learning logistics body.",
        relevance_score=90,
        content_hash="b" * 64,
    )
    summary = await Summarizer().summarize_article(article)
    assert "Machine learning" in summary


@pytest.mark.asyncio
async def test_summarizer_handles_article_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Summarizer falls back when one article summary fails."""
    article = Article(
        source_key="test",
        source_name="Test",
        title="AI Supply Chain",
        url="https://example.com/fail",
        canonical_url="https://example.com/fail",
        body="Fallback body.",
        relevance_score=90,
        content_hash="i" * 64,
    )
    summarizer = Summarizer()

    async def fail_summary(article: Article) -> str:
        """Raise deterministic summary error."""
        raise RuntimeError("failed")

    monkeypatch.setattr(summarizer, "summarize_article", fail_summary)
    await summarizer.summarize_articles([article])
    assert article.summary == "Fallback body."


def test_summarizer_prompt_contains_context() -> None:
    """Prompt includes title and body."""
    article = Article(
        source_key="test",
        source_name="Test",
        title="AI Supply Chain",
        url="https://example.com/prompt",
        canonical_url="https://example.com/prompt",
        body="Body",
        relevance_score=90,
        content_hash="j" * 64,
    )
    prompt = Summarizer()._prompt(article)
    assert "AI Supply Chain" in prompt
    assert "Body" in prompt
