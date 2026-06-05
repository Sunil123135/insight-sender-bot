"""
Module: tests/test_scrapers.py
Purpose: Unit tests for scraper normalization and arXiv parsing
Author: ScrapeSignal Team
Created: 2026-05-10
"""

# Third-party
import pytest

# Local
from src.db.models import SourceConfig
from src.scrapers.apify_scraper import ApifyScraper
from src.scrapers.arxiv_scraper import ArxivScraper
from src.scrapers.manager import ScraperManager


def test_apify_normalize() -> None:
    """Apify rows normalize into article candidates."""
    source = SourceConfig(source_key="a", name="Apify", url="https://example.com")
    row = {"title": "Title", "url": "https://example.com/a", "text": "Body"}
    article = ApifyScraper()._normalize(row, source)
    assert article["title"] == "Title"
    assert article["body"] == "Body"


@pytest.mark.asyncio
async def test_arxiv_entry_to_article(monkeypatch: pytest.MonkeyPatch) -> None:
    """arXiv entry conversion extracts fields."""
    xml = """
    <entry xmlns="http://www.w3.org/2005/Atom">
      <id>https://arxiv.org/abs/1</id>
      <title>AI Supply Chain</title>
      <summary>Machine learning logistics</summary>
      <published>2026-05-10T01:30:00Z</published>
      <author><name>Ada</name></author>
      <link title="pdf" href="https://arxiv.org/pdf/1"/>
    </entry>
    """
    from defusedxml import ElementTree

    async def fake_extract(url: str) -> str:
        """Return fake PDF text."""
        return "PDF"

    scraper = ArxivScraper()
    monkeypatch.setattr(scraper.pdf_parser, "extract_text_from_url", fake_extract)
    article = await scraper._entry_to_article(ElementTree.fromstring(xml))
    assert article["title"] == "AI Supply Chain"
    assert article["author"] == "Ada"


def test_manager_to_article_and_dedupe() -> None:
    """Manager converts candidates and deduplicates them."""
    source = SourceConfig(
        source_key="supplychaindive", name="S", url="https://example.com"
    )
    manager = ScraperManager()
    article = manager._to_article(
        source,
        {
            "title": "AI supply chain logistics",
            "url": "https://example.com/a",
            "body": "machine learning inventory management",
            "raw_metadata": {},
        },
    )
    assert article.relevance_score >= 70
    assert len(manager._dedupe_articles([article])) == 1


@pytest.mark.asyncio
async def test_manager_scrape_all_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Manager handles empty source list."""

    async def fake_upsert(session: object, articles: list[object]) -> int:
        """Return fake saved count."""
        return len(articles)

    async def fake_remember(session: object, hashes: list[str]) -> int:
        """Return fake hash count."""
        return len(hashes)

    monkeypatch.setattr("src.scrapers.manager.upsert_articles", fake_upsert)
    monkeypatch.setattr("src.scrapers.manager.remember_hashes", fake_remember)
    assert await ScraperManager().scrape_all(object(), [], "run") == []  # type: ignore[arg-type]
