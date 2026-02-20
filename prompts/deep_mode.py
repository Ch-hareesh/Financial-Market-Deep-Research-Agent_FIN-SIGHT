"""
prompts/deep_mode.py
FIN-SIGHT – Deep Mode prompt template.
"""

from typing import Any


def build_deep_mode_prompt(
    user_query: str,
    memory: dict[str, Any] | None = None,
    data_block: str = "",
) -> str:
    """
    Build the user-turn message for Deep Mode.

    Injects memory context and instructs the model to produce all 14 mandatory sections.
    """
    memory = memory or {}

    # Build memory context block
    memory_lines = []
    if memory.get("risk_tolerance"):
        memory_lines.append(f"  - Risk Tolerance: {memory['risk_tolerance']}")
    if memory.get("preferred_kpis"):
        memory_lines.append(f"  - Preferred KPIs: {', '.join(memory['preferred_kpis'])}")
    if memory.get("preferred_sectors"):
        memory_lines.append(f"  - Preferred Sectors: {', '.join(memory['preferred_sectors'])}")
    if memory.get("geographic_focus"):
        memory_lines.append(f"  - Geographic Focus: {', '.join(memory['geographic_focus'])}")
    if memory.get("time_horizon"):
        memory_lines.append(f"  - Investment Horizon: {memory['time_horizon']}")
    if memory.get("previously_analyzed"):
        memory_lines.append(
            f"  - Previously Analyzed: {', '.join(memory['previously_analyzed'][-5:])}"
        )

    memory_block = ""
    if memory_lines:
        memory_block = (
            "\n\nUser Profile (stored memory — tailor all analysis to this profile):\n"
            + "\n".join(memory_lines)
        )

    data_section = f"""

{data_block}
""" if data_block else ""

    return f"""
RESEARCH REQUEST — DEEP MODE

{user_query.strip()}
{memory_block}
{data_section}
INSTRUCTIONS:
Produce a full investment research memo with ALL 14 mandatory sections in order.
Base your financial analysis EXCLUSIVELY on the VERIFIED FINANCIAL DATA above when available.
Do not invent or substitute numbers. If a metric shows N/A, state the data gap explicitly.
Do not skip any section. If data is unavailable for a section, state the limitation explicitly.

Required section structure:

# 1. Executive Summary
Concise 3–5 sentence investment stance.

# 2. Investment Thesis
Core bull thesis in 3–5 structured points.

# 3. Financial Breakdown
Cover each of: Revenue Growth, Margins, ROE, Free Cash Flow, Debt Position, Capital Allocation.
Use sub-headings. Do not use narrative prose — use structured data points.

# 4. Peer Benchmarking
Compare against 2–3 named peers on: Revenue Growth, Operating Margin, EV/EBITDA, P/E, ROE.
State "N/A — single company analysis" if comparison data is not available.

# 5. Competitive Positioning
Market share, moat, pricing power, switching costs, competitive threats.

# 6. Risk Analysis
Cover: Operational Risk, Financial Risk, Macro Risk, Regulatory Risk — each as a separate sub-section.

# 7. Scenario & Sensitivity Analysis
Provide table format:
| Scenario | Revenue Impact | Margin Impact | Valuation Impact | Risk Level |
Include minimum: Base Case, Downside Case, Stress Case.

# 8. Bull Case
3–5 specific bull catalysts with reasoning.

# 9. Bear Case
3–5 specific bear risks with reasoning.

# 10. Valuation Perspective
Multiple-based, intrinsic logic, growth justification — each covered.

# 11. Assumptions
List all assumptions made during this analysis. Be explicit and complete.

# 12. Contradiction Check
State whether any management claims conflict with reported numbers.
Format: WARNING: Contradiction Detected — [type] — [description]
Or: No contradictions detected.

# 13. Confidence & Uncertainty
Score: X.XX / 1.00 [HIGH / MEDIUM / LOW]
Rationale: [explain what limits or supports confidence]

# 14. Token Usage & Cost
[This section will be filled in by the system — include a placeholder]

Do not hallucinate any financial number.
Do not use emojis or informal language.
Do not use hype language or marketing tone.
""".strip()
