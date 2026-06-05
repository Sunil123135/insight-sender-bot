"""
Module: src/processors/pdf_parser.py
Purpose: Fetch and extract text from PDFs for arXiv-style sources
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - httpx (async PDF fetching)
    - pdfplumber (PDF text extraction)

Used by:
    - src.scrapers.arxiv_scraper
"""

# Standard library
import asyncio
import logging
from io import BytesIO

# Third-party
import httpx
import pdfplumber

# Local
from src.config import settings
from src.utils.retry import async_retry

logger = logging.getLogger(__name__)


class PDFFetchError(RuntimeError):
    """Raised when PDF fetching or parsing fails."""


class PDFParser:
    """Async PDF fetcher with thread-offloaded text extraction."""

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException, PDFFetchError))
    async def fetch_pdf(self, url: str) -> bytes:
        """Fetch PDF bytes from URL.

        Args:
            url: PDF URL.

        Returns:
            PDF bytes.

        Raises:
            PDFFetchError: If the PDF cannot be fetched.
        """
        timeout = httpx.Timeout(settings.PDF_TIMEOUT_SECONDS, connect=5.0)
        async with httpx.AsyncClient(
            timeout=timeout, headers={"User-Agent": settings.USER_AGENT}
        ) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
            except httpx.HTTPError as error:
                logger.error("PDF fetch failed for %s: %s", url, error, exc_info=True)
                raise PDFFetchError(f"Could not fetch PDF {url}") from error

    async def extract_text_from_url(self, url: str) -> str:
        """Fetch and parse PDF text.

        Args:
            url: PDF URL.

        Returns:
            Extracted text.
        """
        content = await self.fetch_pdf(url)
        return await asyncio.to_thread(self._extract_text, content)

    def _extract_text(self, content: bytes) -> str:
        """Extract text from PDF bytes.

        Args:
            content: PDF bytes.

        Returns:
            Extracted text content.
        """
        with pdfplumber.open(BytesIO(content)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages[:20]]
        text = "\n".join(pages).strip()
        logger.info("Extracted %s characters from PDF", len(text))
        return text
