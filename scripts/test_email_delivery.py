"""
Module: scripts/test_email_delivery.py
Purpose: Send a test ScrapeSignal brief through the Power Automate webhook
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.email.generator (test HTML)
    - src.email.sender (Power Automate delivery)

Used by:
    - Pre-deployment validation
"""

# Standard library
import argparse
import asyncio
from datetime import UTC, datetime

# Local
from src.config import settings
from src.email.generator import EmailGenerator
from src.email.sender import BriefSender
from src.logger import setup_logging


async def send_test() -> None:
    """Send test brief to the configured Power Automate webhook."""
    settings.DRY_RUN = False
    generator = EmailGenerator()
    result = await BriefSender().send(
        generator.subject(datetime.now(UTC)),
        generator.render_test_email(),
        1,
        "test-run",
    )
    print(result)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns:
        Parsed arguments.
    """
    return argparse.ArgumentParser().parse_args()


if __name__ == "__main__":
    setup_logging()
    asyncio.run(send_test())
