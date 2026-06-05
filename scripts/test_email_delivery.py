"""
Module: scripts/test_email_delivery.py
Purpose: Send a test ScrapeSignal email through configured SendGrid account
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.email.generator (test HTML)
    - src.email.sender (SendGrid delivery)

Used by:
    - Pre-deployment validation
"""

# Standard library
import argparse
import asyncio
from datetime import UTC, datetime

# Local
from src.email.generator import EmailGenerator
from src.email.sender import EmailSender
from src.logger import setup_logging


async def send_test(recipient: str) -> None:
    """Send test email.

    Args:
        recipient: Recipient email.
    """
    generator = EmailGenerator()
    result = await EmailSender().send(
        recipient,
        generator.subject(datetime.now(UTC)),
        generator.render_test_email(),
        1,
    )
    print(result)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipient", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    setup_logging()
    asyncio.run(send_test(parse_args().recipient))
