"""
Module: src/processors/summarizer.py
Purpose: Summarize selected articles using Anthropic Claude API
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - httpx (async Anthropic API calls)
    - src.config.py (Claude settings)

Used by:
    - src.main (email article preparation)
"""

# Standard library
import asyncio
import logging

# Third-party
import httpx

# Local
from src.config import settings
from src.db.models import Article
from src.utils.retry import async_retry

logger = logging.getLogger(__name__)

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"


class Summarizer:
    """Claude-powered article summarizer."""

    def __init__(self) -> None:
        """Initialize summarizer rate limiter."""
        self._semaphore = asyncio.Semaphore(settings.CLAUDE_REQUESTS_PER_MINUTE)

    async def summarize_articles(self, articles: list[Article]) -> list[Article]:
        """Summarize articles concurrently with rate limiting.

        Args:
            articles: Articles needing summaries.

        Returns:
            Articles with summaries populated.
        """
        tasks = [self.summarize_article(article) for article in articles]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for article, result in zip(articles, results, strict=True):
            if isinstance(result, Exception):
                logger.error(
                    "Summary failed for %s: %s", article.url, result, exc_info=True
                )
                article.summary = self.fallback_summary(article)
            else:
                article.summary = str(result)
        return articles

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def summarize_article(self, article: Article) -> str:
        """Summarize a single article through Claude.

        Args:
            article: Article to summarize.

        Returns:
            Concise business summary.
        """
        if not settings.secret_is_set(settings.ANTHROPIC_API_KEY) or settings.DRY_RUN:
            return self.fallback_summary(article)

        async with self._semaphore:
            payload = {
                "model": settings.CLAUDE_MODEL,
                "max_tokens": settings.CLAUDE_MAX_TOKENS,
                "messages": [{"role": "user", "content": self._prompt(article)}],
            }
            headers = {
                "x-api-key": settings.ANTHROPIC_API_KEY.get_secret_value(),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            timeout = httpx.Timeout(45.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    ANTHROPIC_MESSAGES_URL, json=payload, headers=headers
                )
                response.raise_for_status()
                data = response.json()
                usage = data.get("usage", {})
                logger.info(
                    "Claude summary usage input_tokens=%s output_tokens=%s",
                    usage.get("input_tokens"),
                    usage.get("output_tokens"),
                )
                content = data["content"][0]["text"]
                return str(content).strip()

    def fallback_summary(self, article: Article) -> str:
        """Create deterministic fallback summary for dry runs or API failures.

        Args:
            article: Article to summarize.

        Returns:
            Short summary string.
        """
        body = " ".join(article.body.split())
        excerpt = body[:240].rstrip()
        return excerpt or article.title

    def _prompt(self, article: Article) -> str:
        """Build Claude prompt for a supply chain executive brief.

        Args:
            article: Article to summarize.

        Returns:
            Prompt text.
        """
        body = article.body[:8_000]
        return (
            "Summarize this article for a Senior Manager at QuidelOrtho focused on "
            "supply chain and AI. Return 2 concise sentences: why it matters and "
            "what to watch next.\n\n"
            f"Title: {article.title}\nSource: {article.source_name}\nBody:\n{body}"
        )
