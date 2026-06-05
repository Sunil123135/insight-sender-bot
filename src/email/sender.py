"""
Module: src/email/sender.py
Purpose: Send ScrapeSignal HTML emails through SendGrid
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - httpx (async SendGrid API call)
    - src.config.py (email settings)

Used by:
    - src.main (orchestrator)
    - scripts/test_email_delivery.py
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

SENDGRID_SEND_URL = "https://api.sendgrid.com/v3/mail/send"


class EmailSendResult(TypedDict):
    """Result from email sending."""

    success: bool
    email_id: str | None
    status_code: int | None
    error: str | None


class EmailSender:
    """Send HTML email through SendGrid."""

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def send(
        self,
        recipient: str,
        subject: str,
        html_content: str,
        article_count: int,
    ) -> EmailSendResult:
        """Send email.

        Args:
            recipient: Recipient email address.
            subject: Email subject.
            html_content: HTML body.
            article_count: Number of articles included.

        Returns:
            Send result.
        """
        masked = self._mask_email(recipient)
        logger.info("Sending email to %s with %s articles", masked, article_count)
        if settings.DRY_RUN:
            logger.info("DRY_RUN=True; email not sent")
            return {
                "success": True,
                "email_id": "dry-run",
                "status_code": 202,
                "error": None,
            }
        if not settings.secret_is_set(settings.SENDGRID_API_KEY):
            return {
                "success": False,
                "email_id": None,
                "status_code": None,
                "error": "SENDGRID_API_KEY missing",
            }

        payload = {
            "personalizations": [{"to": [{"email": recipient}]}],
            "from": {"email": str(settings.SENDER_EMAIL), "name": settings.SENDER_NAME},
            "subject": subject,
            "content": [{"type": "text/html", "value": html_content}],
            "custom_args": {"article_count": str(article_count)},
        }
        headers = {
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY.get_secret_value()}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0)
        ) as client:
            response = await client.post(
                SENDGRID_SEND_URL, json=payload, headers=headers
            )
            response.raise_for_status()
        message_id = response.headers.get("X-Message-Id")
        logger.info("SendGrid accepted email message_id=%s", message_id)
        return {
            "success": True,
            "email_id": message_id,
            "status_code": response.status_code,
            "error": None,
        }

    def _mask_email(self, recipient: str) -> str:
        """Mask email for logs.

        Args:
            recipient: Email address.

        Returns:
            Masked email.
        """
        local, _, domain = recipient.partition("@")
        return f"{local[:3]}***@{domain}" if domain else "***"
