"""
Module: src/main.py
Purpose: ScrapeSignal pipeline orchestrator
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.db (database sessions)
    - src.scrapers.manager (scrape orchestration)
    - src.email.* (render, validate, send)
    - src.processors.summarizer (Claude summaries)

Used by:
    - GitHub Actions daily workflow
    - Docker entrypoint
    - Manual dry runs
"""

# Standard library
import argparse
import asyncio
import logging
import uuid
from datetime import UTC, datetime

# Local
from src.config import settings
from src.db.models import Article, EmailLog
from src.db.repository import (
    get_enabled_keywords,
    get_enabled_sources,
    mark_articles_emailed,
    purge_expired_hashes,
    select_top_articles,
)
from src.db.session import get_db
from src.email.generator import EmailGenerator
from src.email.sender import BriefSender
from src.email.validator import EmailValidator
from src.logger import setup_logging
from src.processors.scorer import RelevanceScorer
from src.processors.summarizer import Summarizer
from src.scrapers.manager import ScraperManager
from src.utils.slack_alerts import send_slack_alert

logger = logging.getLogger(__name__)


class ScrapeSignalOrchestrator:
    """Coordinate the full ScrapeSignal daily run."""

    def __init__(self) -> None:
        """Initialize orchestrator dependencies."""
        self.email_generator = EmailGenerator()
        self.email_validator = EmailValidator()
        self.brief_sender = BriefSender()
        self.summarizer = Summarizer()

    async def run(self) -> int:
        """Execute the complete scrape to email pipeline.

        Returns:
            Process exit code.
        """
        run_id = self._new_run_id()
        started = datetime.now(UTC)
        logger.info("ScrapeSignal run %s starting", run_id)
        try:
            if settings.ENVIRONMENT == "production" and not settings.DRY_RUN:
                settings.validate_for_production()

            async with get_db() as session:
                await purge_expired_hashes(session)
                keywords = await get_enabled_keywords(session)
                sources = await get_enabled_sources(session)

            # Scraping performs long network I/O; keep it outside an open transaction
            # so Neon does not terminate idle-in-transaction sessions.
            async with get_db() as session:
                manager = ScraperManager(RelevanceScorer(keywords))
                await manager.scrape_all(session, sources, run_id)

            articles = await self.summarizer.summarize_articles(
                await self._load_top_articles()
            )
            html = self.email_generator.render(articles, run_id, started)
            validation = self.email_validator.validate(html)
            if validation["link_issues"] or validation["alt_text_issues"]:
                logger.warning("Email validation issues: %s", validation)
            subject = self.email_generator.subject(started)
            result = await self.brief_sender.send(
                subject,
                html,
                len(articles),
                run_id,
            )

            async with get_db() as session:
                session.add(
                    EmailLog(
                        run_id=run_id,
                        recipient_email="power-automate-webhook",
                        subject=subject,
                        article_count=len(articles),
                        status="success" if result["success"] else "failed",
                        sendgrid_message_id=result["delivery_id"],
                        error_message=result["error"],
                        sent_at=(datetime.now(UTC) if result["success"] else None),
                    ),
                )
                if result["success"]:
                    await mark_articles_emailed(session, articles, datetime.now(UTC))
            duration = (datetime.now(UTC) - started).total_seconds()
            logger.info(
                "ScrapeSignal run %s completed in %.2f seconds", run_id, duration
            )
            return 0
        except Exception as error:
            logger.critical(
                "ScrapeSignal run %s failed: %s", run_id, error, exc_info=True
            )
            await send_slack_alert(f"Run {run_id} failed: {error}", severity="critical")
            return 1

    async def _load_top_articles(self) -> list[Article]:
        """Load ranked articles for the daily brief.

        Returns:
            Top articles selected from the database.
        """
        async with get_db() as session:
            return await select_top_articles(session)

    def _new_run_id(self) -> str:
        """Create unique run identifier.

        Returns:
            Run identifier.
        """
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return f"{stamp}-{uuid.uuid4().hex[:8]}"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Run ScrapeSignal pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Force dry run behavior")
    return parser.parse_args()


async def async_main() -> int:
    """Async CLI entrypoint.

    Returns:
        Process exit code.
    """
    args = parse_args()
    if args.dry_run:
        settings.DRY_RUN = True
    setup_logging()
    orchestrator = ScrapeSignalOrchestrator()
    return await orchestrator.run()


def main() -> None:
    """Synchronous console entrypoint."""
    raise SystemExit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
