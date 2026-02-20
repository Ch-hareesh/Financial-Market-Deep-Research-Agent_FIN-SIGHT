"""
prompts/quick_mode.py
FIN-SIGHT – Quick Mode prompt template.
"""

from typing import Any


def build_quick_mode_prompt(
    user_query: str,
    memory: dict[str, Any] | None = None,
    data_block: str = "",
) -> str:
    """
    Build the user-turn message for Quick Mode.

    Injects memory context if available so the model can tailor its output.
    """
    memory = memory or {}

    memory_context = ""
    if memory.get("risk_tolerance") or memory.get("preferred_kpis"):
        parts = []
        if memory.get("risk_tolerance"):
            parts.append(f"Risk Tolerance: {memory['risk_tolerance']}")
        if memory.get("preferred_kpis"):
            parts.append(f"Preferred KPIs: {', '.join(memory['preferred_kpis'])}")
        if memory.get("time_horizon"):
            parts.append(f"Time Horizon: {memory['time_horizon']}")
        if parts:
            memory_context = (
                "\n\nUser Profile (stored memory):\n"
                + "\n".join(f"  - {p}" for p in parts)
                + "\n\nTailor the analysis to the above user profile."
            )

    data_section = f"""

{data_block}
""" if data_block else ""

    return f"""
RESEARCH REQUEST — QUICK MODE

{user_query.strip()}
{memory_context}{data_section}
INSTRUCTIONS:
Return a structured Quick Mode output as bullet points using this exact format:

• **Company:** [company name and ticker]
• **Reporting Period:** [specific quarter and fiscal year, e.g. Q4 FY2024]
• **Revenue:** [value with unit, e.g. $95.4B]
• **YoY Growth:** [percentage]
• **EBITDA:** [value with unit]
• **Net Profit:** [value with unit]
• **Gross Margin:** [percentage]
• **Operating Margin:** [percentage]
• **Free Cash Flow:** [value with unit]
• **Market Cap:** [value]
• **P/E Ratio:** [value]x
• **Key Risks:** [2–3 short bullet phrases, comma-separated]
• **Management Guidance:** [one sentence or "Not disclosed"]
• **Notable Changes:** [one sentence or "None"]
• **Confidence Score:** [0.00–1.00]
• **Data Gaps:** [list fields that are unavailable, or "None"]

After the bullets, add a blank line and then a 2–3 sentence analyst summary paragraph.

DATA USAGE RULES:
- Use the VERIFIED FINANCIAL DATA above as the primary source for all numbers.
- For any field not in the verified data, use training knowledge and state the reporting period.
- If genuinely unknown, write "Not available".
- NEVER invent numbers. Use approximate ranges (e.g. "~$38B–$40B") if unsure.

Keep output concise and factual. No emojis. No marketing language.
""".strip()
