"""
Module: src/processors/summarizer.py
Purpose: Summarize selected articles using Groq with Gemini fallbacks
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - httpx (async LLM API calls)
    - src.config.py (LLM settings)

Used by:
    - src.main (brief article preparation)
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

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_GENERATE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class Summarizer:
    """Groq-first summarizer with Gemini Flash fallbacks."""

    def __init__(self) -> None:
        """Initialize summarizer rate limiter."""
        self._semaphore = asyncio.Semaphore(settings.LLM_REQUESTS_PER_MINUTE)

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

    async def summarize_article(self, article: Article) -> str:
        """Summarize a single article through Groq then Gemini fallbacks.

        Args:
            article: Article to summarize.

        Returns:
            Concise business summary.
        """
        if settings.DRY_RUN:
            return self.fallback_summary(article)

        prompt = self._prompt(article)
        async with self._semaphore:
            if settings.secret_is_set(settings.GROQ_API_KEY):
                try:
                    return await self._summarize_with_groq(prompt)
                except Exception as error:
                    logger.warning("Groq summary failed: %s", error)

            for model in settings.gemini_fallback_models():
                if not settings.secret_is_set(settings.GEMINI_API_KEY):
                    break
                try:
                    return await self._summarize_with_gemini(prompt, model)
                except Exception as error:
                    logger.warning("Gemini summary failed for %s: %s", model, error)

        return self.fallback_summary(article)

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def _summarize_with_groq(self, prompt: str) -> str:
        """Summarize through Groq chat completions API.

        Args:
            prompt: Prompt text.

        Returns:
            Generated summary.
        """
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": settings.LLM_MAX_TOKENS,
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY.get_secret_value()}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(45.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(GROQ_CHAT_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        logger.info("Groq summary generated with model=%s", settings.GROQ_MODEL)
        return str(content).strip()

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def _summarize_with_gemini(self, prompt: str, model: str) -> str:
        """Summarize through Gemini generateContent API.

        Args:
            prompt: Prompt text.
            model: Gemini model id.

        Returns:
            Generated summary.
        """
        url = GEMINI_GENERATE_URL.format(model=model)
        params = {"key": settings.GEMINI_API_KEY.get_secret_value()}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": settings.LLM_MAX_TOKENS},
        }
        timeout = httpx.Timeout(45.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(str(part.get("text", "")) for part in parts)
        logger.info("Gemini summary generated with model=%s", model)
        return text.strip()

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
        """Build summary prompt for a supply chain executive brief.

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
