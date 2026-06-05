"""
Module: src/email/generator.py
Purpose: Render ScrapeSignal daily brief HTML with Jinja2
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - jinja2 (template rendering)
    - src.config.py (email settings)
    - src.db.models.py (Article model)

Used by:
    - src.main (orchestrator)
    - scripts/preview_email.py
"""

# Standard library
from datetime import UTC, datetime
from pathlib import Path

# Third-party
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Local
from src.config import settings
from src.db.models import Article


class EmailGenerator:
    """Render HTML email briefs."""

    def __init__(self) -> None:
        """Initialize Jinja environment."""
        template_dir = Path(__file__).parent
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render(
        self, articles: list[Article], run_id: str, report_date: datetime
    ) -> str:
        """Render daily brief HTML.

        Args:
            articles: Selected articles.
            run_id: Pipeline run identifier.
            report_date: Report date.

        Returns:
            HTML email string.
        """
        template = self.env.get_template("template.html")
        subject = self.subject(report_date)
        return template.render(
            articles=articles,
            run_id=run_id,
            report_date=report_date.strftime("%A, %B %d, %Y"),
            subject=subject,
            threshold=settings.MIN_RELEVANCE_SCORE,
        )

    def render_test_email(self) -> str:
        """Render deterministic sample email.

        Returns:
            HTML string with two test articles.
        """
        articles = [
            Article(
                source_key="test",
                source_name="Supply Chain Dive",
                title="AI improves supply chain resilience in healthcare logistics",
                url="https://example.com/article",
                canonical_url="https://example.com/article",
                body=(
                    "Machine learning is improving inventory planning and "
                    "distribution reliability."
                ),
                summary=(
                    "AI planning tools can reduce supply disruptions and "
                    "improve service levels."
                ),
                relevance_score=95.0,
                content_hash="a" * 64,
            ),
        ]
        return self.render(articles, "test-run", datetime.now(UTC))

    def subject(self, report_date: datetime) -> str:
        """Build email subject.

        Args:
            report_date: Report date.

        Returns:
            Subject line.
        """
        date_text = report_date.strftime("%b %d, %Y")
        return f"{settings.EMAIL_SUBJECT_PREFIX} - {date_text}"
