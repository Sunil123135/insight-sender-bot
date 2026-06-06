"""
Module: tests/test_email_sender.py
Purpose: Unit tests for async Power Automate brief delivery
Author: ScrapeSignal Team
Created: 2026-05-10
"""

# Third-party
import pytest

# Local
from src.email.sender import BriefSender


@pytest.mark.asyncio
async def test_brief_sender_dry_run() -> None:
    """Dry run returns success without network."""
    result = await BriefSender().send("Subject", "<p>Body</p>", 1, "run-1")
    assert result["success"] is True
    assert result["delivery_id"] == "dry-run"
