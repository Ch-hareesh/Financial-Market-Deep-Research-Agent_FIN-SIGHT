"""
src/output_formatter.py
FIN-SIGHT – Structured output renderer.
Formats Quick Mode and Deep Mode outputs into production-grade financial memo style.
All output adheres to brandGuidelines: no emojis, no casual language, structured sections only.
"""

from __future__ import annotations
from typing import Any

from src.contradiction_detector import format_contradiction_block
from src.confidence_engine import format_confidence_block, ConfidenceResult
from src.cost_tracker import UsageSummary
from src.scenario_engine import format_scenario_table, ScenarioRow


# ---------------------------------------------------------------------------
# Separator constant
# ---------------------------------------------------------------------------
_SEP = "-" * 72


def format_quick_mode(
    model_response: str,
    cost_summary: UsageSummary,
    company: str = "N/A",
    period: str = "N/A",
    confidence_result: ConfidenceResult | None = None,
    contradictions: list[dict] | None = None,
) -> str:
    """
    Render a Quick Mode structured output block.
    If model_response already contains all fields, it is used as-is under the header.
    """
    contradictions = contradictions or []
    lines = [
        _SEP,
        "FIN-SIGHT  |  RESEARCH MEMO  |  QUICK MODE",
        _SEP,
        "",
        model_response.strip(),
        "",
    ]

    # Contradiction flag (if detected)
    if contradictions:
        lines.append(_SEP)
        lines.append("CONTRADICTION ALERT")
        lines.append(format_contradiction_block(contradictions))
        lines.append("")

    # Confidence block
    if confidence_result:
        lines.append(_SEP)
        lines.append("CONFIDENCE & UNCERTAINTY")
        lines.append(format_confidence_block(confidence_result))
        lines.append("")

    # Cost block — mandatory
    lines.append(_SEP)
    lines.append("TOKEN USAGE & COST")
    lines.append(cost_summary.format())
    lines.append(_SEP)

    return "\n".join(lines)


def format_deep_mode(
    sections: dict[str, str],
    scenario_rows: list[ScenarioRow],
    confidence_result: ConfidenceResult,
    cost_summary: UsageSummary,
    contradictions: list[dict] | None = None,
) -> str:
    """
    Render a full Deep Mode structured financial memo.

    The model is instructed to write all 14 sections itself in its response.
    We render that response directly, then append system-generated blocks
    (contradiction check, confidence score, cost summary) so they are always
    present and consistently formatted regardless of model output.
    """
    contradictions = contradictions or []

    # The model's full response (all 14 sections it wrote)
    model_output = sections.get("executive_summary", "").strip()

    lines: list[str] = [
        "=" * 72,
        "FIN-SIGHT  |  INVESTMENT RESEARCH MEMO  |  DEEP MODE",
        "=" * 72,
        f"Generated: {_get_timestamp()}",
        "",
        model_output,
        "",
    ]

    # --- System-generated: Contradiction Check (always appended) ---
    lines += [
        "=" * 72,
        "SYSTEM: CONTRADICTION CHECK",
        "=" * 72,
    ]
    if contradictions:
        lines.append("WARNING: Contradictions Detected")
        lines.append(format_contradiction_block(contradictions))
    else:
        lines.append(format_contradiction_block([]))

    # --- System-generated: Confidence & Uncertainty (always appended) ---
    lines += [
        "",
        "=" * 72,
        "SYSTEM: CONFIDENCE & UNCERTAINTY",
        "=" * 72,
        format_confidence_block(confidence_result),
    ]

    # --- System-generated: Token Usage & Cost (mandatory) ---
    lines += [
        "",
        "=" * 72,
        "SYSTEM: TOKEN USAGE & COST",
        "=" * 72,
        cost_summary.format(),
        "=" * 72,
    ]

    return "\n".join(lines)


def format_scenario_only(
    scenario_rows: list[ScenarioRow],
    cost_summary: UsageSummary,
    trigger: str = "",
) -> str:
    """
    Format a standalone scenario re-run output (e.g., 'Re-evaluate under high inflation').
    Only the scenario section is rendered.
    """
    lines = [
        _SEP,
        "FIN-SIGHT  |  SCENARIO RE-RUN",
        f"Trigger: {trigger}" if trigger else "",
        _SEP,
        "",
        format_scenario_table(scenario_rows),
        "",
        _SEP,
        "TOKEN USAGE & COST",
        cost_summary.format(),
        _SEP,
    ]
    return "\n".join(l for l in lines if l is not None)


def _get_timestamp() -> str:
    """Return current UTC timestamp string."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
