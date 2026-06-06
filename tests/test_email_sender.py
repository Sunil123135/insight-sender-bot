"""Unit tests for Power Automate brief delivery."""

# Third-party
import pytest

# Local
from src.email.sender import BriefSender, SUBJECT_HEADER


@pytest.mark.asyncio
async def test_brief_sender_dry_run() -> None:
    """Dry run returns success without network."""
    result = await BriefSender().send("Subject", "<p>Body</p>", 1, "run-1")
    assert result["success"] is True
    assert result["delivery_id"] == "dry-run"


def test_json_payload_uses_body_and_is_html() -> None:
    """JSON mode exposes Outlook-friendly body and isHtml fields."""
    payload = BriefSender()._json_payload(
        "Subject line",
        "<html><body><p>Hello</p></body></html>",
        3,
        "run-1",
    )
    assert payload["subject"] == "Subject line"
    assert payload["body"] == "<html><body><p>Hello</p></body></html>"
    assert payload["isHtml"] is True


def test_html_headers_include_subject() -> None:
    """HTML mode sends subject in a dedicated header."""
    headers = BriefSender()._html_headers(
        "Subject line",
        "<html><body>Hello</body></html>",
        2,
        "run-2",
    )
    assert headers[SUBJECT_HEADER] == "Subject line"
    assert headers["Content-Type"] == "text/html; charset=utf-8"
