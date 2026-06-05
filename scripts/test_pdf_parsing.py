"""
Module: scripts/test_pdf_parsing.py
Purpose: Smoke-test PDF parsing against a provided URL
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.processors.pdf_parser (PDF parsing)

Used by:
    - Local validation
"""

# Standard library
import argparse
import asyncio

# Local
from src.processors.pdf_parser import PDFParser


async def run(url: str) -> None:
    """Parse a PDF URL and print extracted character count.

    Args:
        url: PDF URL.
    """
    text = await PDFParser().extract_text_from_url(url)
    print(f"Extracted {len(text)} characters")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://arxiv.org/pdf/1706.03762")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args().url))
