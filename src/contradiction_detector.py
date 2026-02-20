"""
src/contradiction_detector.py
FIN-SIGHT – Contradiction detection module.
Identifies mismatches between management guidance/narratives and reported numbers.
All checks are rule-based and operate on structured financial data dicts.
"""

from __future__ import annotations
from typing import Any


def detect_contradictions(financial_data: dict[str, Any]) -> list[dict[str, str]]:
    """
    Scan financial_data for logical contradictions.

    Expected financial_data keys (all optional — missing keys are skipped):
        revenue_growth_reported  : float   (e.g. 0.12 for 12% YoY growth)
        revenue_growth_guided    : float   (management's stated growth guidance)
        operating_margin_current : float   (current period, e.g. 0.22 for 22%)
        operating_margin_prior   : float   (prior period)
        margin_improvement_claim : bool    (management claimed margin improved)
        total_debt_current       : float   (USD millions)
        total_debt_prior         : float   (prior period, USD millions)
        debt_reduction_claim     : bool    (management claimed debt was reduced)
        net_income_current       : float
        net_income_prior         : float
        profitability_claim      : bool    (management claimed profitability improved)
        fcf_current              : float   (free cash flow, may be negative)
        claims                   : list[str]  (free-text management claims for text checks)

    Returns:
        List of contradiction dicts, each with keys:
            type        : str
            description : str
            severity    : "HIGH" | "MEDIUM"
    """
    contradictions: list[dict[str, str]] = []
    d = financial_data

    # ------------------------------------------------------------------
    # 1. Revenue growth guidance vs actual growth mismatch
    # ------------------------------------------------------------------
    reported_growth = d.get("revenue_growth_reported")
    guided_growth = d.get("revenue_growth_guided")
    if reported_growth is not None and guided_growth is not None:
        deviation = reported_growth - guided_growth
        if abs(deviation) >= 0.05:  # >= 5 percentage point gap
            direction = "above" if deviation > 0 else "below"
            severity = "HIGH" if abs(deviation) >= 0.10 else "MEDIUM"
            contradictions.append({
                "type": "Revenue Guidance vs Actual Mismatch",
                "description": (
                    f"Management guided {guided_growth:.1%} revenue growth; "
                    f"actual reported growth was {reported_growth:.1%} "
                    f"({abs(deviation):.1%} {direction} guidance)."
                ),
                "severity": severity,
            })

    # ------------------------------------------------------------------
    # 2. Margin expansion claim vs declining margins
    # ------------------------------------------------------------------
    margin_claim = d.get("margin_improvement_claim")
    margin_current = d.get("operating_margin_current")
    margin_prior = d.get("operating_margin_prior")
    if margin_claim is True and margin_current is not None and margin_prior is not None:
        if margin_current < margin_prior:
            drop = margin_prior - margin_current
            contradictions.append({
                "type": "Margin Improvement Claim vs Declining Margins",
                "description": (
                    f"Management claimed margin improvement, but operating margin "
                    f"contracted from {margin_prior:.1%} to {margin_current:.1%} "
                    f"(a decline of {drop:.1%})."
                ),
                "severity": "HIGH",
            })

    # ------------------------------------------------------------------
    # 3. Debt reduction claim vs rising leverage
    # ------------------------------------------------------------------
    debt_claim = d.get("debt_reduction_claim")
    debt_current = d.get("total_debt_current")
    debt_prior = d.get("total_debt_prior")
    if debt_claim is True and debt_current is not None and debt_prior is not None:
        if debt_current > debt_prior:
            increase = debt_current - debt_prior
            contradictions.append({
                "type": "Debt Reduction Claim vs Rising Leverage",
                "description": (
                    f"Management stated debt was reduced, but total debt increased "
                    f"from {debt_prior:,.0f}M to {debt_current:,.0f}M "
                    f"(+{increase:,.0f}M)."
                ),
                "severity": "HIGH",
            })

    # ------------------------------------------------------------------
    # 4. Profitability improvement claim vs declining net income
    # ------------------------------------------------------------------
    profit_claim = d.get("profitability_claim")
    ni_current = d.get("net_income_current")
    ni_prior = d.get("net_income_prior")
    if profit_claim is True and ni_current is not None and ni_prior is not None:
        if ni_current < ni_prior:
            drop = ni_prior - ni_current
            contradictions.append({
                "type": "Profitability Claim vs Declining Net Income",
                "description": (
                    f"Management claimed improved profitability, but net income fell "
                    f"from {ni_prior:,.0f}M to {ni_current:,.0f}M "
                    f"(a decline of {drop:,.0f}M)."
                ),
                "severity": "MEDIUM",
            })

    # ------------------------------------------------------------------
    # 5. Positive FCF claim (from claims list) while FCF is negative
    # ------------------------------------------------------------------
    fcf = d.get("fcf_current")
    claims = d.get("claims", []) or []
    fcf_positive_claimed = any(
        kw in c.lower()
        for c in claims
        for kw in ["strong free cash flow", "positive fcf", "cash generation", "cash conversion"]
    )
    if fcf_positive_claimed and fcf is not None and fcf < 0:
        contradictions.append({
            "type": "Positive FCF Claim vs Negative FCF",
            "description": (
                f"Management referenced strong cash generation, "
                f"but reported FCF is negative ({fcf:,.0f}M)."
            ),
            "severity": "HIGH",
        })

    return contradictions


def format_contradiction_block(contradictions: list[dict[str, str]]) -> str:
    """
    Format the contradiction list for structured output.
    Returns an empty string if no contradictions were found.
    """
    if not contradictions:
        return "No contradictions detected between reported numbers and management statements."

    lines = []
    for i, c in enumerate(contradictions, start=1):
        lines.append(f"  [{i}] {c['type']}  |  Severity: {c['severity']}")
        lines.append(f"      {c['description']}")
    return "\n".join(lines)
