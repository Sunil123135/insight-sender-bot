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

Power Automate mapping (json mode):
    - Subject: @triggerBody()?['subject']
    - Body: @triggerBody()?['body']
    - Is HTML: Yes
"""

# Standard library
import logging
from typing import TypedDict

# Third-party
import httpx

# Local
from src.config import settings
from src.utils.retry import async_retry

logger = logging.getLogger(__name__)

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

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
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

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0)
        ) as client:
            if settings.POWER_AUTOMATE_PAYLOAD_FORMAT == "json":
                response = await client.post(
                    webhook_url,
                    json=self._json_payload(
                        subject, html_content, article_count, run_id
                    ),
                )
            else:
                response = await client.post(
                    webhook_url,
                    content=html_content.encode("utf-8"),
                    headers=self._html_headers(
                        subject, html_content, article_count, run_id
                    ),
                )
            response.raise_for_status()

        delivery_id = response.headers.get("x-ms-request-id") or response.headers.get(
            "x-request-id"
        )
        logger.info(
            "Power Automate accepted brief status=%s delivery_id=%s format=%s",
            response.status_code,
            delivery_id,
            settings.POWER_AUTOMATE_PAYLOAD_FORMAT,
        )
        return {
            "success": True,
            "delivery_id": delivery_id,
            "status_code": response.status_code,
            "error": None,
        }

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
