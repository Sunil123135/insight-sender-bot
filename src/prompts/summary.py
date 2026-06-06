"""Prompt templates for article analysis summaries."""

SUMMARY_SYSTEM_INSTRUCTIONS = """You are a Supply Chain Innovation Advisor.

Read the article and identify only insights that could drive measurable improvements in:
- Service Levels
- Inventory
- Working Capital
- Forecast Accuracy
- OTIF
- Productivity
- Cost-to-Serve
- Supply Risk
- Customer Experience

For each insight provide:

1. Insight
2. Potential Supply Chain Use Case
3. Expected Benefit
4. Difficulty (Low/Medium/High)
5. Time Horizon (0-6 months, 6-18 months, 18+ months)

Then provide:

### Executive Summary (max 100 words)

### Top 3 Recommended Actions

### AI Opportunity Score (1-10)

### Supply Chain Impact Score (1-10)

Be concise and focus on actions rather than description."""


def build_summary_prompt(*, title: str, source_name: str, body: str) -> str:
    """Build the full user prompt for article analysis.

    Args:
        title: Article headline.
        source_name: Source display name.
        body: Article body text (already truncated by caller if needed).

    Returns:
        Complete prompt string for the LLM.
    """
    return (
        f"{SUMMARY_SYSTEM_INSTRUCTIONS}\n\n"
        f"Title: {title}\n"
        f"Source: {source_name}\n"
        f"Body:\n{body}"
    )
