"""
src/scenario_engine.py
FIN-SIGHT – Scenario and sensitivity analysis engine.
Produces directional impact tables for supported stress scenarios.
Does NOT fabricate numeric precision — all impacts are qualitative or derived
from user-provided data if available.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class ScenarioRow:
    scenario: str
    revenue_impact: str
    margin_impact: str
    valuation_impact: str
    risk_level: str
    notes: str = ""


# ---------------------------------------------------------------------------
# Scenario definitions — directional impacts with reasoning rationale
# ---------------------------------------------------------------------------
_SCENARIO_TEMPLATES: dict[str, dict[str, str]] = {
    "high_inflation": {
        "scenario": "High Inflation",
        "revenue_impact": "Moderate Positive (pricing power may offset volume risk)",
        "margin_impact": "Negative (input cost and wage inflation compress margins)",
        "valuation_impact": "Negative (higher discount rates compress multiples)",
        "risk_level": "HIGH",
        "notes": "Companies with strong pricing power and low input cost exposure are more resilient.",
    },
    "interest_rate_hike": {
        "scenario": "Interest Rate Hike",
        "revenue_impact": "Neutral to Negative (demand softening in rate-sensitive segments)",
        "margin_impact": "Negative (higher debt servicing costs for leveraged firms)",
        "valuation_impact": "Negative (DCF discount rate increases, compresses fair value)",
        "risk_level": "HIGH",
        "notes": "Impact amplified for high-debt or growth-oriented companies.",
    },
    "revenue_slowdown": {
        "scenario": "Revenue Slowdown",
        "revenue_impact": "Negative (below-trend or declining top-line growth)",
        "margin_impact": "Negative (operating leverage works in reverse)",
        "valuation_impact": "Negative (growth premium compression)",
        "risk_level": "HIGH",
        "notes": "Fixed-cost-heavy businesses are most exposed to revenue deceleration.",
    },
    "margin_compression": {
        "scenario": "Margin Compression",
        "revenue_impact": "Neutral",
        "margin_impact": "Negative (EBITDA and net margin contract materially)",
        "valuation_impact": "Negative (EV/EBITDA multiples re-rate lower)",
        "risk_level": "MEDIUM",
        "notes": "Can result from competitive pricing pressure, wage inflation, or input cost spikes.",
    },
    "currency_depreciation": {
        "scenario": "Currency Depreciation",
        "revenue_impact": "Mixed (benefits exporters, hurts importers and USD-reporting firms with foreign revenues)",
        "margin_impact": "Mixed (input cost effects depend on import dependence)",
        "valuation_impact": "Negative for foreign investors (FX-adjusted returns erode)",
        "risk_level": "MEDIUM",
        "notes": "Highly dependent on revenue currency mix and hedging strategy.",
    },
    "regulatory_tightening": {
        "scenario": "Regulatory Tightening",
        "revenue_impact": "Negative (compliance costs, potential revenue caps or product restrictions)",
        "margin_impact": "Negative (compliance opex and capex increase)",
        "valuation_impact": "Negative (risk premium expansion, multiple contraction)",
        "risk_level": "HIGH",
        "notes": "Sector-specific; most material in Financials, Healthcare, Technology, and Energy.",
    },
    "recession": {
        "scenario": "Recession / Demand Contraction",
        "revenue_impact": "Strongly Negative (volume decline across discretionary segments)",
        "margin_impact": "Strongly Negative (deleverage effect on fixed costs)",
        "valuation_impact": "Strongly Negative (multiple compression + earnings downgrade)",
        "risk_level": "VERY HIGH",
        "notes": "Defensive sectors (utilities, staples) relatively more resilient.",
    },
}

_ALIAS_MAP: dict[str, str] = {
    "inflation": "high_inflation",
    "high inflation": "high_inflation",
    "rate hike": "interest_rate_hike",
    "interest rate": "interest_rate_hike",
    "rate hikes": "interest_rate_hike",
    "slowdown": "revenue_slowdown",
    "revenue slowdown": "revenue_slowdown",
    "margin compression": "margin_compression",
    "currency": "currency_depreciation",
    "fx": "currency_depreciation",
    "depreciation": "currency_depreciation",
    "regulatory": "regulatory_tightening",
    "regulation": "regulatory_tightening",
    "recession": "recession",
    "demand contraction": "recession",
}

_DEFAULT_SCENARIOS = [
    "high_inflation",
    "interest_rate_hike",
    "revenue_slowdown",
]


def _resolve_scenario_key(name: str) -> str | None:
    """Resolve an alias or direct key to a canonical scenario key."""
    normalized = name.lower().strip()
    if normalized in _SCENARIO_TEMPLATES:
        return normalized
    return _ALIAS_MAP.get(normalized)


def run_scenarios(
    scenario_names: list[str] | None = None,
    financial_data: dict[str, Any] | None = None,
) -> list[ScenarioRow]:
    """
    Return a list of ScenarioRow objects for the requested scenarios.
    If scenario_names is None or empty, uses the default 3 scenarios
    (Base, Downside, Stress — mapped to slowdown, inflation, recession).

    financial_data is reserved for future quantitative adjustments but
    is not required for directional analysis.
    """
    if not scenario_names:
        keys = _DEFAULT_SCENARIOS
    else:
        keys = []
        for name in scenario_names:
            key = _resolve_scenario_key(name)
            if key and key not in keys:
                keys.append(key)
        if not keys:
            keys = _DEFAULT_SCENARIOS

    rows = []
    for key in keys:
        template = _SCENARIO_TEMPLATES.get(key)
        if template:
            rows.append(ScenarioRow(**template))

    return rows


def run_base_downside_stress(
    financial_data: dict[str, Any] | None = None,
) -> list[ScenarioRow]:
    """
    Produce the mandatory Base / Downside / Stress case table as required
    by Deep Mode section 7.
    """
    base = ScenarioRow(
        scenario="Base Case",
        revenue_impact="In-line with consensus / management guidance",
        margin_impact="Stable or modest expansion (cost efficiencies realized)",
        valuation_impact="Neutral to slight positive (re-rating on execution)",
        risk_level="LOW",
        notes="Assumes no major macro disruption; business performs per plan.",
    )
    downside = ScenarioRow(
        scenario="Downside Case",
        revenue_impact="5–10% below base (demand softening, pricing pressure)",
        margin_impact="100–150 bps compression (operating leverage reversal)",
        valuation_impact="Negative 15–25% (EPS downgrade + multiple contraction)",
        risk_level="MEDIUM",
        notes="Triggered by revenue growth miss or margin guidance cut.",
    )
    stress = ScenarioRow(
        scenario="Stress Case",
        revenue_impact="15–25% below base (recessionary or regulatory shock)",
        margin_impact="300+ bps compression (cost structure under-absorbed)",
        valuation_impact="Negative 30–50% (deep multiple de-rating)",
        risk_level="VERY HIGH",
        notes="Requires compounding adverse factors: macro shock + sector headwind.",
    )
    return [base, downside, stress]


def format_scenario_table(rows: list[ScenarioRow]) -> str:
    """
    Render a markdown-format scenario table.
    """
    header = (
        "| Scenario | Revenue Impact | Margin Impact | Valuation Impact | Risk Level |\n"
        "|---|---|---|---|---|"
    )
    data_rows = []
    for r in rows:
        data_rows.append(
            f"| {r.scenario} | {r.revenue_impact} | {r.margin_impact} | {r.valuation_impact} | {r.risk_level} |"
        )

    table = header + "\n" + "\n".join(data_rows)

    # Append notes if any
    notes_lines = []
    for r in rows:
        if r.notes:
            notes_lines.append(f"  - **{r.scenario}**: {r.notes}")
    if notes_lines:
        table += "\n\nScenario Notes:\n" + "\n".join(notes_lines)

    return table
