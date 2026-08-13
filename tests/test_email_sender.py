"""Unit tests for Power Automate brief delivery."""

# Standard library
from unittest.mock import AsyncMock

# Third-party
import httpx
import pytest

# Local
from src.email.sender import BriefSender, SUBJECT_HEADER


def _response(status_code: int, text: str = "", request_id: str = "req-1") -> httpx.Response:
    """Build a fake Power Automate HTTP response."""
    request = httpx.Request("POST", "https://example.com/pa")
    return httpx.Response(
        status_code=status_code,
        text=text,
        headers={"x-ms-request-id": request_id},
        request=request,
    )


@pytest.mark.asyncio
async def test_brief_sender_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dry run returns success without network."""
    from src.config import settings

    monkeypatch.setattr(settings, "DRY_RUN", True)
    result = await BriefSender().send("Subject", "<p>Body</p>", 1, "run-1")
    assert result["success"] is True
    assert result["delivery_id"] == "dry-run"


@pytest.mark.asyncio
async def test_html_400_falls_back_to_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 400 from HTML mode retries with JSON instead of failing the run."""
    from src.config import settings

    monkeypatch.setattr(settings, "DRY_RUN", False)
    monkeypatch.setattr(settings, "POWER_AUTOMATE_WEBHOOK_URL", "https://example.com/pa")
    monkeypatch.setattr(settings, "POWER_AUTOMATE_PAYLOAD_FORMAT", "html")

    sender = BriefSender()
    formats: list[str] = []

    async def fake_post(
        client: httpx.AsyncClient,
        fmt: str,
        webhook_url: str,
        subject: str,
        html_content: str,
        article_count: int,
        run_id: str | None,
    ) -> httpx.Response:
        formats.append(fmt)
        if fmt == "html":
            return _response(400, '{"error":{"code":"InvalidRequest"}}')
        return _response(202, "")

    monkeypatch.setattr(sender, "_post_format", fake_post)
    result = await sender.send("Subject", "<html><body>Hi</body></html>", 2, "run-2")
    assert formats == ["html", "json"]
    assert result["success"] is True
    assert result["status_code"] == 202
    assert result["delivery_id"] == "req-1"


@pytest.mark.asyncio
async def test_all_formats_rejected_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Both payload formats returning 400 still fail delivery."""
    from src.config import settings

    monkeypatch.setattr(settings, "DRY_RUN", False)
    monkeypatch.setattr(settings, "POWER_AUTOMATE_WEBHOOK_URL", "https://example.com/pa")
    monkeypatch.setattr(settings, "POWER_AUTOMATE_PAYLOAD_FORMAT", "html")

    sender = BriefSender()
    sender._post_format = AsyncMock(  # type: ignore[method-assign]
        side_effect=[
            _response(400, "html rejected"),
            _response(400, "json rejected"),
        ]
    )
    with pytest.raises(httpx.HTTPStatusError):
        await sender.send("Subject", "<html><body>Hi</body></html>", 1, "run-3")


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
