"""
src/clarification.py
FIN-SIGHT – Interactive clarification layer.
Determines if user memory is sufficient to proceed, and surfaces the minimum
set of clarifying questions needed before DEEP MODE analysis.
"""

from __future__ import annotations
from typing import Any


# ---------------------------------------------------------------------------
# Clarification question bank
# ---------------------------------------------------------------------------
_DEEP_MODE_QUESTIONS: list[dict[str, str]] = [
    {
        "key": "time_horizon",
        "question": "What is your investment horizon? (e.g., 1 year, 3 years, long-term)",
    },
    {
        "key": "risk_tolerance",
        "question": "What is your risk tolerance? (Conservative, Moderate, or Aggressive)",
    },
    {
        "key": "scenario_focus",
        "question": "Should I stress-test this analysis under inflation and/or recession scenarios?",
    },
    {
        "key": "valuation_method",
        "question": "Do you prefer intrinsic valuation (DCF-logic) or peer multiple comparison (EV/EBITDA, P/E)?",
    },
]

_REQUIRED_FOR_DEEP: list[str] = ["risk_tolerance", "time_horizon"]


def needs_clarification(query: str, memory: dict[str, Any], mode: str) -> bool:
    """
    Returns True if important context is missing before DEEP MODE analysis
    and the query does not already supply it inline.

    Clarification is skipped when:
    - Mode is QUICK
    - Memory already has all required fields populated
    - The query itself contains enough context signals
    """
    if mode != "DEEP":
        return False

    normalized = query.lower()
    missing = _get_missing_keys(memory)

    # Consider the query itself as providing context inline
    inline_risk = any(
        token in normalized
        for token in ["conservative", "moderate", "aggressive", "risk"]
    )
    inline_horizon = any(
        token in normalized
        for token in ["year", "years", "horizon", "short-term", "long-term", "term"]
    )

    if "risk_tolerance" in missing and not inline_risk:
        return True
    if "time_horizon" in missing and not inline_horizon:
        return True

    return False


def get_clarification_questions(memory: dict[str, Any]) -> list[str]:
    """
    Return a filtered list of clarification questions for fields not yet stored in memory.
    Only returns questions for fields actually missing from memory.
    """
    missing = _get_missing_keys(memory)
    questions = []
    for item in _DEEP_MODE_QUESTIONS:
        if item["key"] in missing:
            questions.append(item["question"])
    return questions


def format_clarification_prompt(questions: list[str]) -> str:
    """
    Format the clarification questions into a structured, professional request.
    """
    if not questions:
        return ""

    lines = [
        "Before proceeding with the full analysis, please provide the following information:",
        "",
    ]
    for i, q in enumerate(questions, start=1):
        lines.append(f"  {i}. {q}")
    lines.append(
        "\nThese inputs ensure the analysis is calibrated to your objectives and risk profile."
    )
    return "\n".join(lines)


def _get_missing_keys(memory: dict[str, Any]) -> list[str]:
    """Return required memory keys that are None or empty."""
    missing = []
    for key in _REQUIRED_FOR_DEEP:
        val = memory.get(key)
        if not val:
            missing.append(key)
    return missing


def extract_preferences_from_input(user_input: str) -> dict[str, Any]:
    """
    Attempt to parse stated preferences from freeform user input and return
    a dict of key-value pairs suitable for updating memory.

    This is a rule-based extractor — no ML inference.
    """
    normalized = user_input.lower()
    prefs: dict[str, Any] = {}

    # Risk tolerance
    if "conservative" in normalized:
        prefs["risk_tolerance"] = "Conservative"
    elif "aggressive" in normalized:
        prefs["risk_tolerance"] = "Aggressive"
    elif "moderate" in normalized:
        prefs["risk_tolerance"] = "Moderate"

    # Time horizon — extract duration mentions
    import re
    horizon_match = re.search(
        r"(\d+[\-\s]?(?:year|yr|month|week)s?(?:\s+horizon)?)", normalized
    )
    if horizon_match:
        prefs["time_horizon"] = horizon_match.group(1).strip()
    elif "long-term" in normalized or "long term" in normalized:
        prefs["time_horizon"] = "Long-term"
    elif "short-term" in normalized or "short term" in normalized:
        prefs["time_horizon"] = "Short-term"

    # KPI preferences
    kpi_map = {
        "roe": "ROE",
        "ebitda": "EBITDA",
        "free cash flow": "FCF",
        "fcf": "FCF",
        "net margin": "Net Margin",
        "revenue cagr": "Revenue CAGR",
        "eps": "EPS",
        "p/e": "P/E",
    }
    kpis_found = [label for token, label in kpi_map.items() if token in normalized]
    if kpis_found:
        prefs["preferred_kpis"] = kpis_found

    # Sector preferences — basic keyword match
    sector_map = {
        "technology": "Technology",
        "tech": "Technology",
        "healthcare": "Healthcare",
        "finance": "Financials",
        "financial": "Financials",
        "energy": "Energy",
        "consumer": "Consumer",
        "industrial": "Industrials",
        "real estate": "Real Estate",
    }
    sectors_found = [label for token, label in sector_map.items() if token in normalized]
    if sectors_found:
        prefs["preferred_sectors"] = sectors_found

    return prefs
