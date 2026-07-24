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

Return ONLY valid JSON (no markdown fences, no prose outside JSON) with this exact shape:

{
  "executive_summary": "Max 60 words. What matters and why for a supply chain leader.",
  "insights": [
    {
      "insight": "One crisp insight (max 18 words)",
      "use_case": "Specific supply chain use case (max 12 words)",
      "benefit": "Expected measurable benefit (max 12 words)",
      "difficulty": "Low|Medium|High",
      "time_horizon": "0-6 months|6-18 months|18+ months"
    }
  ],
  "actions": [
    "Action 1 (imperative, max 16 words)",
    "Action 2",
    "Action 3"
  ],
  "ai_opportunity_score": 1,
  "supply_chain_impact_score": 1
}

Rules:
- Include 2 to 3 insights maximum (highest signal only).
- Exactly 3 actions.
- Scores are integers from 1 to 10.
- Be concise and action-oriented. Do not repeat the article."""


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
