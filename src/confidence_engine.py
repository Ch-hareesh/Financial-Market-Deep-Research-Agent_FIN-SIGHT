"""
src/confidence_engine.py
FIN-SIGHT – Confidence scoring engine.
Produces a 0.0–1.0 confidence score and a rationale string based on
data completeness, source count, and contradictions detected.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ConfidenceResult:
    score: float              # 0.0 (lowest) to 1.0 (highest)
    grade: str                # HIGH | MEDIUM | LOW
    rationale: str            # Human-readable explanation
    deductions: list[str]     # List of individual deduction reasons


# ---------------------------------------------------------------------------
# Scoring constants — additive deductions from a baseline of 1.0
# ---------------------------------------------------------------------------
_MISSING_DATA_PENALTY: float = 0.10      # per missing required field
_CONTRADICTION_PENALTY: float = 0.12     # per detected contradiction
_HIGH_SEVERITY_BONUS_PENALTY: float = 0.05  # additional if severity is HIGH
_SINGLE_SOURCE_PENALTY: float = 0.08    # only one data source provided
_UNVERIFIED_GUIDANCE_PENALTY: float = 0.05  # management guidance not cross-checked

_SCORE_FLOOR: float = 0.10  # minimum possible score


def calculate_confidence(
    data_completeness: float,          # 0.0–1.0: fraction of expected fields present
    contradictions: list[dict],        # output from contradiction_detector
    source_count: int,                 # number of distinct data sources provided
    guidance_verified: bool = False,   # True if management guidance was cross-checked
) -> ConfidenceResult:
    """
    Calculate a confidence score from 0.0 to 1.0.

    Parameters:
        data_completeness : fraction of required financial fields present (0.0–1.0)
        contradictions    : list of contradiction dicts from contradiction_detector
        source_count      : number of distinct data sources
        guidance_verified : whether management guidance was cross-checked

    Returns:
        ConfidenceResult
    """
    score = 1.0
    deductions: list[str] = []

    # --- Data completeness deduction ---
    missing_fraction = max(0.0, 1.0 - data_completeness)
    if missing_fraction > 0:
        penalty = round(missing_fraction * _MISSING_DATA_PENALTY * 5, 4)
        score -= penalty
        pct = round(missing_fraction * 100)
        deductions.append(f"Data completeness: {100 - pct}% — deducted {penalty:.2f}")

    # --- Contradiction deductions ---
    for c in contradictions:
        penalty = _CONTRADICTION_PENALTY
        if c.get("severity", "").upper() == "HIGH":
            penalty += _HIGH_SEVERITY_BONUS_PENALTY
        score -= penalty
        deductions.append(
            f"Contradiction ({c.get('severity', 'UNKNOWN')}): {c.get('type', 'N/A')} — deducted {penalty:.2f}"
        )

    # --- Single data source penalty ---
    if source_count <= 1:
        score -= _SINGLE_SOURCE_PENALTY
        deductions.append(f"Single data source — deducted {_SINGLE_SOURCE_PENALTY:.2f}")

    # --- Unverified guidance penalty ---
    if not guidance_verified:
        score -= _UNVERIFIED_GUIDANCE_PENALTY
        deductions.append(
            f"Management guidance not independently verified — deducted {_UNVERIFIED_GUIDANCE_PENALTY:.2f}"
        )

    # --- Apply floor ---
    score = max(_SCORE_FLOOR, round(score, 2))

    # --- Grade ---
    if score >= 0.75:
        grade = "HIGH"
    elif score >= 0.50:
        grade = "MEDIUM"
    else:
        grade = "LOW"

    # --- Rationale summary ---
    if not deductions:
        rationale = "All required fields present, no contradictions detected, multiple sources, guidance verified."
    else:
        rationale = (
            f"Confidence reduced due to: {'; '.join(deductions[:3])}"
            + ("." if len(deductions) <= 3 else f"; and {len(deductions) - 3} additional factor(s).")
        )

    return ConfidenceResult(
        score=score,
        grade=grade,
        rationale=rationale,
        deductions=deductions,
    )


def format_confidence_block(result: ConfidenceResult) -> str:
    """Return a structured text block for embedding in output."""
    lines = [
        "Confidence Score  : {:.2f} / 1.00  [{}]".format(result.score, result.grade),
        "Rationale         :",
    ]
    if result.deductions:
        for d in result.deductions:
            lines.append(f"  - {d}")
    else:
        lines.append(f"  {result.rationale}")
    return "\n".join(lines)
