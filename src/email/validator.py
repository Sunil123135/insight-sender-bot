"""
Module: src/email/validator.py
Purpose: Validate generated HTML email for basic deliverability and accessibility
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - beautifulsoup4 (HTML parsing)

Used by:
    - src.main (pre-send validation)
    - tests/test_email.py
"""

# Standard library
from typing import TypedDict

# Third-party
from bs4 import BeautifulSoup


class EmailValidationResult(TypedDict):
    """Email validation issue buckets."""

    alt_text_issues: list[str]
    link_issues: list[str]
    html_size_bytes: int


class EmailValidator:
    """Validate rendered email HTML."""

    def validate(self, html: str) -> EmailValidationResult:
        """Validate HTML.

        Args:
            html: Rendered HTML email.

        Returns:
            Validation result dictionary.
        """
        soup = BeautifulSoup(html, "html.parser")
        alt_text_issues = [
            str(index)
            for index, image in enumerate(soup.find_all("img"), start=1)
            if not image.get("alt")
        ]
        link_issues = [
            str(link.get_text(" ", strip=True) or index)
            for index, link in enumerate(soup.find_all("a"), start=1)
            if not str(link.get("href", "")).startswith(("http://", "https://"))
        ]
        return {
            "alt_text_issues": alt_text_issues,
            "link_issues": link_issues,
            "html_size_bytes": len(html.encode("utf-8")),
        }
