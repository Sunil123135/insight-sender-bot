"""
Module: tests/test_summary_format.py
Purpose: Unit tests for structured summary HTML formatting
Author: ScrapeSignal Team
Created: 2026-07-24
"""

# Local
from src.email.summary_format import format_summary_html


def test_format_summary_html_renders_structured_json() -> None:
    """JSON summaries become scannable email sections."""
    raw = """
    {
      "executive_summary": "Simulation-first planning can cut cost-to-serve.",
      "insights": [
        {
          "insight": "Pair simulation with OR to dispose weak plans early",
          "use_case": "End-to-end supply planning",
          "benefit": "Better service at lower cost",
          "difficulty": "Medium",
          "time_horizon": "6-18 months"
        }
      ],
      "actions": [
        "Pilot SPORD on one planning lane",
        "Measure OTIF and planner cycle time",
        "Scale after 2 planning cycles"
      ],
      "ai_opportunity_score": 8,
      "supply_chain_impact_score": 9
    }
    """
    html = format_summary_html(raw)
    assert "Executive summary" in html
    assert "Simulation-first planning" in html
    assert "Key insights" in html
    assert "Pair simulation with OR" in html
    assert "Recommended actions" in html
    assert "AI opportunity 8/10" in html
    assert "SC impact 9/10" in html
    assert "**" not in html


def test_format_summary_html_escapes_plain_text() -> None:
    """Plain fallback text is escaped for email safety."""
    html = format_summary_html('Alert <script>alert("x")</script> & more')
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&amp; more" in html


def test_format_summary_html_parses_legacy_markdown() -> None:
    """Older markdown advisor blobs become the same card layout."""
    raw = (
        "Here are the insights: 1. **Insight**: Pair simulation with OR "
        "**Potential Supply Chain Use Case**: End-to-end planning "
        "**Expected Benefit**: Better service levels "
        "**Difficulty**: Medium **Time Horizon**: 6-18 months "
        "### Executive Summary (max 100 words)\n"
        "SPORD can improve planning efficiency.\n"
        "### Top 3 Recommended Actions\n"
        "1. Pilot SPORD on one lane\n"
        "2. Measure OTIF weekly\n"
        "3. Scale after two cycles\n"
        "### AI Opportunity Score (1-10)\n8\n"
        "### Supply Chain Impact Score (1-10)\n9\n"
    )
    html = format_summary_html(raw)
    assert "Executive summary" in html
    assert "SPORD can improve planning efficiency." in html
    assert "Key insights" in html
    assert "Pair simulation with OR" in html
    assert "Recommended actions" in html
    assert "Pilot SPORD on one lane" in html
    assert "AI opportunity 8/10" in html
    assert "**Insight**" not in html
