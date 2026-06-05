"""
Module: tests/test_email_sender.py
Purpose: Unit tests for async SendGrid sender
Author: ScrapeSignal Team
Created: 2026-05-10
"""

# Third-party
import pytest

# Local
from src.email.sender import EmailSender


@pytest.mark.asyncio
async def test_email_sender_dry_run() -> None:
    """Dry run returns success without network."""
    result = await EmailSender().send("test@example.com", "Subject", "<p>Body</p>", 1)
    assert result["success"] is True
    assert result["email_id"] == "dry-run"
