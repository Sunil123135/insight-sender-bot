"""
Module: src/utils/slack_alerts.py
Purpose: Send ScrapeSignal operational alerts to Slack webhooks
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - httpx (async webhook delivery)
    - src.config.py (Slack settings)

Used by:
    - src.main (failure alerting)
"""

# Standard library
import logging

# Third-party
import httpx

# Local
from src.config import settings
from src.utils.retry import async_retry

logger = logging.getLogger(__name__)

SEVERITY_ORDER: dict[str, int] = {
    "info": 10,
    "warning": 20,
    "error": 30,
    "critical": 40,
}


@async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
async def send_slack_alert(message: str, severity: str = "error") -> None:
    """Send Slack alert when webhook is configured.

    Args:
        message: Alert text.
        severity: Alert severity.
    """
    configured_threshold = SEVERITY_ORDER[settings.SLACK_ALERT_SEVERITY_THRESHOLD]
    if SEVERITY_ORDER.get(severity, 30) < configured_threshold:
        return
    if not settings.secret_is_set(settings.SLACK_WEBHOOK_URL):
        logger.warning("Slack webhook missing; alert suppressed severity=%s", severity)
        return
    payload = {"text": f"[ScrapeSignal][{severity.upper()}] {message}"}
    webhook_url = settings.SLACK_WEBHOOK_URL.get_secret_value()
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
        response = await client.post(webhook_url, json=payload)
        response.raise_for_status()
    logger.info("Slack alert delivered severity=%s", severity)
