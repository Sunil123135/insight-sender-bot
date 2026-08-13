"""
Module: src/email/sender.py
Purpose: Deliver ScrapeSignal HTML briefs through a Power Automate webhook
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - httpx (async webhook POST)
    - src.config.py (delivery settings)

Used by:
    - src.main (orchestrator)
    - scripts/test_email_delivery.py

Power Automate mapping (recommended, html mode):
    - Subject: @triggerOutputs()?['headers']['X-Email-Subject']
    - Body: @triggerBody()
    - Is HTML: Yes

Power Automate mapping (json mode / automatic fallback after HTML 400):
    - Subject: @triggerBody()?['subject']
    - Body: @triggerBody()?['body']
    - Is HTML: Yes
"""

# Standard library
import logging
from typing import Literal, TypedDict

# Third-party
import httpx

# Local
from src.config import settings

logger = logging.getLogger(__name__)

PayloadFormat = Literal["html", "json"]

SUBJECT_HEADER = "X-Email-Subject"
ARTICLE_COUNT_HEADER = "X-Article-Count"
RUN_ID_HEADER = "X-Run-Id"


class BriefDeliveryResult(TypedDict):
    """Result from brief delivery."""

    success: bool
    delivery_id: str | None
    status_code: int | None
    error: str | None


class BriefSender:
    """Send the daily HTML brief to a Power Automate webhook."""

    async def send(
        self,
        subject: str,
        html_content: str,
        article_count: int,
        run_id: str | None = None,
    ) -> BriefDeliveryResult:
        """POST the HTML brief to Power Automate.

        Args:
            subject: Brief subject line.
            html_content: HTML body.
            article_count: Number of articles included.
            run_id: Optional pipeline run identifier.

        Returns:
            Delivery result.
        """
        logger.info(
            "Delivering brief to Power Automate with %s articles", article_count
        )
        if settings.DRY_RUN:
            logger.info("DRY_RUN=True; brief not delivered")
            return {
                "success": True,
                "delivery_id": "dry-run",
                "status_code": 202,
                "error": None,
            }

        webhook_url = settings.POWER_AUTOMATE_WEBHOOK_URL.strip()
        if not webhook_url:
            return {
                "success": False,
                "delivery_id": None,
                "status_code": None,
                "error": "POWER_AUTOMATE_WEBHOOK_URL missing",
            }

        formats = self._format_order()
        last_response: httpx.Response | None = None
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0)
        ) as client:
            for fmt in formats:
                response = await self._post_format(
                    client,
                    fmt,
                    webhook_url,
                    subject,
                    html_content,
                    article_count,
                    run_id,
                )
                last_response = response
                if response.is_success or response.status_code == 202:
                    delivery_id = response.headers.get(
                        "x-ms-request-id"
                    ) or response.headers.get("x-request-id")
                    logger.info(
                        "Power Automate accepted brief status=%s delivery_id=%s format=%s",
                        response.status_code,
                        delivery_id,
                        fmt,
                    )
                    return {
                        "success": True,
                        "delivery_id": delivery_id,
                        "status_code": response.status_code,
                        "error": None,
                    }
                logger.warning(
                    "Power Automate rejected format=%s status=%s body=%s",
                    fmt,
                    response.status_code,
                    (response.text or "")[:500],
                )
                if response.status_code >= 500:
                    response.raise_for_status()

        assert last_response is not None
        last_response.raise_for_status()
        raise RuntimeError("Power Automate delivery failed without HTTP error")

    def _format_order(self) -> list[PayloadFormat]:
        """Return preferred payload formats, with the other format as fallback.

        Returns:
            Payload formats to attempt in order.
        """
        preferred: PayloadFormat = (
            "json" if settings.POWER_AUTOMATE_PAYLOAD_FORMAT == "json" else "html"
        )
        fallback: PayloadFormat = "html" if preferred == "json" else "json"
        return [preferred, fallback]

    async def _post_format(
        self,
        client: httpx.AsyncClient,
        fmt: PayloadFormat,
        webhook_url: str,
        subject: str,
        html_content: str,
        article_count: int,
        run_id: str | None,
    ) -> httpx.Response:
        """POST one payload format to the Power Automate webhook.

        Args:
            client: Shared HTTP client.
            fmt: Payload format to send.
            webhook_url: Webhook URL.
            subject: Brief subject line.
            html_content: HTML body.
            article_count: Number of articles included.
            run_id: Optional pipeline run identifier.

        Returns:
            HTTP response.
        """
        if fmt == "json":
            return await client.post(
                webhook_url,
                json=self._json_payload(subject, html_content, article_count, run_id),
            )
        return await client.post(
            webhook_url,
            content=html_content.encode("utf-8"),
            headers=self._html_headers(subject, html_content, article_count, run_id),
        )

    def _html_headers(
        self,
        subject: str,
        html_content: str,
        article_count: int,
        run_id: str | None,
    ) -> dict[str, str]:
        """Build headers for raw HTML webhook delivery.

        Args:
            subject: Email subject.
            html_content: HTML body.
            article_count: Number of articles.
            run_id: Optional run id.

        Returns:
            HTTP request headers.
        """
        headers = {
            "Content-Type": "text/html; charset=utf-8",
            SUBJECT_HEADER: subject,
            ARTICLE_COUNT_HEADER: str(article_count),
        }
        if run_id:
            headers[RUN_ID_HEADER] = run_id
        if html_content.startswith("<!DOCTYPE") or html_content.startswith("<html"):
            headers["Content-Type"] = "text/html; charset=utf-8"
        return headers

    def _json_payload(
        self,
        subject: str,
        html_content: str,
        article_count: int,
        run_id: str | None,
    ) -> dict[str, object]:
        """Build JSON payload for Power Automate email mapping.

        Args:
            subject: Email subject.
            html_content: HTML body.
            article_count: Number of articles.
            run_id: Optional run id.

        Returns:
            JSON-serializable webhook body.
        """
        payload: dict[str, object] = {
            "subject": subject,
            "body": html_content,
            "html_content": html_content,
            "isHtml": True,
            "article_count": article_count,
        }
        if run_id:
            payload["run_id"] = run_id
        return payload
