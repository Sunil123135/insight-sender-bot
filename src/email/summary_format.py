"""
Module: src/email/summary_format.py
Purpose: Parse LLM article summaries into scannable email HTML
Author: ScrapeSignal Team
Created: 2026-07-24
"""

# Standard library
from __future__ import annotations

import html
import json
import re
from typing import Any


def format_summary_html(raw: str | None) -> str:
    """Convert a raw summary (JSON or plain text) into email-safe HTML.

    Args:
        raw: LLM summary text or fallback excerpt.

    Returns:
        HTML fragment safe for email clients.
    """
    text = (raw or "").strip()
    if not text:
        return ""

    parsed = _try_parse_json(text)
    if parsed is None:
        parsed = _try_parse_legacy_markdown(text)
    if parsed is not None:
        return _render_structured(parsed)

    return (
        f'<p style="margin:0;font-size:15px;line-height:23px;color:#263244;">'
        f"{html.escape(text)}</p>"
    )


def _try_parse_json(text: str) -> dict[str, Any] | None:
    """Extract and parse a JSON object from LLM output.

    Args:
        text: Raw model output.

    Returns:
        Parsed dictionary or None when parsing fails.
    """
    candidate = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", candidate, re.IGNORECASE)
    if fence:
        candidate = fence.group(1).strip()

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        data = json.loads(candidate[start : end + 1])
    except json.JSONDecodeError:
        return None

    return data if isinstance(data, dict) else None


def _try_parse_legacy_markdown(text: str) -> dict[str, Any] | None:
    """Parse the previous markdown-style advisor summary into structured fields.

    Args:
        text: Raw markdown-like summary from older prompts.

    Returns:
        Structured dictionary or None when no recognizable sections exist.
    """
    if "**Insight**" not in text and "Executive Summary" not in text:
        return None

    result: dict[str, Any] = {
        "executive_summary": "",
        "insights": [],
        "actions": [],
        "ai_opportunity_score": None,
        "supply_chain_impact_score": None,
    }

    insight_pattern = re.compile(
        r"\*\*Insight\*\*:\s*(.*?)\s*"
        r"\*\*Potential Supply Chain Use Case\*\*:\s*(.*?)\s*"
        r"\*\*Expected Benefit\*\*:\s*(.*?)\s*"
        r"\*\*Difficulty\*\*:\s*(.*?)\s*"
        r"\*\*Time Horizon\*\*:\s*(.*?)(?=\s*(?:\d+\.\s*\*\*Insight\*\*|###|$))",
        re.IGNORECASE | re.DOTALL,
    )
    for match in insight_pattern.finditer(text):
        result["insights"].append(
            {
                "insight": _clean_fragment(match.group(1)),
                "use_case": _clean_fragment(match.group(2)),
                "benefit": _clean_fragment(match.group(3)),
                "difficulty": _clean_fragment(match.group(4)),
                "time_horizon": _clean_fragment(match.group(5)),
            }
        )

    exec_match = re.search(
        r"###\s*Executive Summary[^\n]*\n+(.*?)(?=\n###|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if exec_match:
        result["executive_summary"] = _clean_fragment(exec_match.group(1))

    actions_match = re.search(
        r"###\s*Top\s*3\s*Recommended Actions\s*\n+(.*?)(?=\n###|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if actions_match:
        actions: list[str] = []
        for line in actions_match.group(1).splitlines():
            cleaned = re.sub(r"^\s*\d+\.\s*", "", line).strip()
            if cleaned:
                actions.append(_clean_fragment(cleaned))
        result["actions"] = actions[:3]

    ai_match = re.search(
        r"###\s*AI Opportunity Score[^\n]*\n+\s*(\d{1,2})",
        text,
        re.IGNORECASE,
    )
    if ai_match:
        result["ai_opportunity_score"] = int(ai_match.group(1))

    impact_match = re.search(
        r"###\s*Supply Chain Impact Score[^\n]*\n+\s*(\d{1,2})",
        text,
        re.IGNORECASE,
    )
    if impact_match:
        result["supply_chain_impact_score"] = int(impact_match.group(1))

    has_content = bool(
        result["executive_summary"]
        or result["insights"]
        or result["actions"]
        or result["ai_opportunity_score"] is not None
        or result["supply_chain_impact_score"] is not None
    )
    return result if has_content else None


def _clean_fragment(value: str) -> str:
    """Normalize a captured markdown fragment.

    Args:
        value: Raw captured text.

    Returns:
        Compact plain text.
    """
    cleaned = re.sub(r"\*\*|__", "", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" \t\r\n-•")
    return cleaned


def _render_structured(data: dict[str, Any]) -> str:
    """Render structured summary fields as email HTML.

    Args:
        data: Parsed summary dictionary.

    Returns:
        HTML fragment.
    """
    parts: list[str] = []

    executive = str(data.get("executive_summary") or "").strip()
    if executive:
        parts.append(
            '<div style="margin:0 0 14px 0;padding:12px 14px;background:#f3f7fc;'
            'border-left:3px solid #123e73;border-radius:0 6px 6px 0;">'
            '<div style="font-size:11px;line-height:14px;font-weight:700;'
            'letter-spacing:.06em;text-transform:uppercase;color:#66758a;'
            'margin-bottom:6px;">Executive summary</div>'
            f'<div style="font-size:15px;line-height:23px;color:#18202f;">'
            f"{html.escape(executive)}</div></div>"
        )

    insights = data.get("insights")
    if isinstance(insights, list) and insights:
        rows: list[str] = []
        for item in insights[:3]:
            if not isinstance(item, dict):
                continue
            insight = str(item.get("insight") or "").strip()
            if not insight:
                continue
            use_case = str(item.get("use_case") or "").strip()
            benefit = str(item.get("benefit") or "").strip()
            difficulty = str(item.get("difficulty") or "").strip()
            horizon = str(item.get("time_horizon") or "").strip()

            meta_bits = [
                bit
                for bit in (
                    f"<strong>Use case:</strong> {html.escape(use_case)}"
                    if use_case
                    else "",
                    f"<strong>Benefit:</strong> {html.escape(benefit)}"
                    if benefit
                    else "",
                    f"<strong>Difficulty:</strong> {html.escape(difficulty)}"
                    if difficulty
                    else "",
                    f"<strong>Horizon:</strong> {html.escape(horizon)}"
                    if horizon
                    else "",
                )
                if bit
            ]
            meta = (
                f'<div style="margin-top:4px;font-size:13px;line-height:19px;'
                f'color:#526070;">{" · ".join(meta_bits)}</div>'
                if meta_bits
                else ""
            )
            rows.append(
                '<tr><td style="padding:0 0 12px 0;vertical-align:top;">'
                f'<div style="font-size:14px;line-height:21px;color:#18202f;'
                f'font-weight:700;">{html.escape(insight)}</div>{meta}</td></tr>'
            )

        if rows:
            parts.append(
                '<div style="margin:0 0 14px 0;">'
                '<div style="font-size:11px;line-height:14px;font-weight:700;'
                'letter-spacing:.06em;text-transform:uppercase;color:#66758a;'
                'margin-bottom:8px;">Key insights</div>'
                f'<table role="presentation" width="100%" cellspacing="0" '
                f'cellpadding="0">{"".join(rows)}</table></div>'
            )

    actions = data.get("actions")
    if isinstance(actions, list):
        action_items = [
            str(action).strip() for action in actions if str(action).strip()
        ][:3]
        if action_items:
            lis = "".join(
                f'<li style="margin:0 0 6px 0;">{html.escape(action)}</li>'
                for action in action_items
            )
            parts.append(
                '<div style="margin:0 0 14px 0;">'
                '<div style="font-size:11px;line-height:14px;font-weight:700;'
                'letter-spacing:.06em;text-transform:uppercase;color:#66758a;'
                'margin-bottom:8px;">Recommended actions</div>'
                f'<ol style="margin:0;padding-left:18px;font-size:14px;'
                f'line-height:21px;color:#263244;">{lis}</ol></div>'
            )

    score_chips: list[str] = []
    ai_score = _as_score(data.get("ai_opportunity_score"))
    impact_score = _as_score(data.get("supply_chain_impact_score"))
    if ai_score is not None:
        score_chips.append(_score_chip("AI opportunity", ai_score))
    if impact_score is not None:
        score_chips.append(_score_chip("SC impact", impact_score))
    if score_chips:
        parts.append(
            f'<div style="margin:2px 0 0 0;">{"".join(score_chips)}</div>'
        )

    if not parts:
        return (
            '<p style="margin:0;font-size:15px;line-height:23px;color:#263244;">'
            "Summary unavailable.</p>"
        )
    return "".join(parts)


def _as_score(value: Any) -> int | None:
    """Normalize a score value to an int in 1..10.

    Args:
        value: Raw score value.

    Returns:
        Integer score or None.
    """
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    if score < 1 or score > 10:
        return None
    return score


def _score_chip(label: str, score: int) -> str:
    """Render a compact score badge.

    Args:
        label: Badge label.
        score: Score from 1 to 10.

    Returns:
        HTML span.
    """
    return (
        f'<span style="display:inline-block;margin:0 8px 6px 0;padding:5px 10px;'
        f'background:#eef3f9;border:1px solid #d5deea;border-radius:999px;'
        f'font-size:12px;line-height:16px;color:#31445d;font-weight:700;">'
        f"{html.escape(label)} {score}/10</span>"
    )
