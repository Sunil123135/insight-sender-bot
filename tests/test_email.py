"""
Module: tests/test_email.py
Purpose: Unit tests for email rendering and validation
Author: ScrapeSignal Team
Created: 2026-05-10
"""

# Local
from src.email.generator import EmailGenerator
from src.email.validator import EmailValidator


def test_email_template_renders() -> None:
    """Test email renders valid HTML shell."""
    html = EmailGenerator().render_test_email()
    assert "<!DOCTYPE html>" in html
    assert "ScrapeSignal Daily Brief" in html


def test_email_validator_passes_links() -> None:
    """Rendered test email has valid links."""
    html = EmailGenerator().render_test_email()
    result = EmailValidator().validate(html)
    assert result["link_issues"] == []
    assert result["html_size_bytes"] > 1000
