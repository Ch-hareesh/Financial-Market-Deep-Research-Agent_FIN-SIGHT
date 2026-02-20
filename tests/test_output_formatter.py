"""
tests/test_output_formatter.py
Unit tests for src/output_formatter.py
"""

import pytest
from src.output_formatter import format_quick_mode, format_deep_mode, format_scenario_only
from src.cost_tracker import estimate_cost
from src.confidence_engine import ConfidenceResult
from src.scenario_engine import run_base_downside_stress


def _make_confidence(score: float = 0.75) -> ConfidenceResult:
    grade = "HIGH" if score >= 0.75 else ("MEDIUM" if score >= 0.50 else "LOW")
    return ConfidenceResult(
        score=score,
        grade=grade,
        rationale="Test rationale.",
        deductions=[],
    )


def _make_usage():
    return estimate_cost(1000, 500, latency_ms=1200)


class TestFormatQuickMode:

    def test_returns_string(self):
        usage = _make_usage()
        output = format_quick_mode("Company: Apple\nRevenue: $90B", usage)
        assert isinstance(output, str)

    def test_contains_finsight_header(self):
        usage = _make_usage()
        output = format_quick_mode("Revenue: $90B", usage)
        assert "FIN-SIGHT" in output

    def test_contains_quick_mode_label(self):
        usage = _make_usage()
        output = format_quick_mode("Revenue: $90B", usage)
        assert "QUICK MODE" in output

    def test_contains_token_section(self):
        usage = _make_usage()
        output = format_quick_mode("Revenue: $90B", usage)
        assert "TOKEN USAGE" in output or "Prompt Tokens" in output

    def test_contains_cost(self):
        usage = _make_usage()
        output = format_quick_mode("Revenue: $90B", usage)
        assert "Estimated Cost" in output

    def test_contains_confidence_when_provided(self):
        usage = _make_usage()
        confidence = _make_confidence(0.80)
        output = format_quick_mode("Revenue: $90B", usage, confidence_result=confidence)
        assert "Confidence Score" in output or "0.80" in output

    def test_contradiction_alert_when_present(self):
        usage = _make_usage()
        contradictions = [
            {"type": "Revenue Mismatch", "description": "Guided 15% grew 3%.", "severity": "HIGH"}
        ]
        output = format_quick_mode("Revenue: $90B", usage, contradictions=contradictions)
        assert "CONTRADICTION" in output or "Revenue Mismatch" in output

    def test_no_emojis_in_output(self):
        usage = _make_usage()
        output = format_quick_mode("Revenue: $90B", usage)
        # Check for common emojis
        for emoji_char in ["🚀", "📊", "💰", "✅", "❌", "⚠️"]:
            assert emoji_char not in output


class TestFormatDeepMode:

    def _build_sections(self) -> dict:
        return {
            "executive_summary": "Test company showed strong results.",
            "investment_thesis": "Thesis point 1. Thesis point 2.",
            "financial_breakdown": "Revenue: $10B. Margin: 25%.",
            "competitive_positioning": "Market leader in segment.",
            "risk_analysis": "Operational: supply chain. Macro: inflation.",
            "bull_case": "Strong FCF. Market expansion.",
            "bear_case": "Margin compression risk. Competition.",
            "valuation_perspective": "EV/EBITDA 12x. Fair value $150.",
            "assumptions": "1. Revenue growth steady. 2. No major regulatory change.",
        }

    def test_returns_string(self):
        sections = self._build_sections()
        rows = run_base_downside_stress()
        usage = _make_usage()
        confidence = _make_confidence(0.72)
        output = format_deep_mode(sections, rows, confidence, usage)
        assert isinstance(output, str)

    def test_contains_all_14_section_numbers(self):
        sections = self._build_sections()
        rows = run_base_downside_stress()
        usage = _make_usage()
        confidence = _make_confidence(0.72)
        output = format_deep_mode(sections, rows, confidence, usage)
        for i in range(1, 15):
            assert f"SECTION {i}:" in output, f"Missing SECTION {i}"

    def test_contains_executive_summary(self):
        sections = self._build_sections()
        rows = run_base_downside_stress()
        usage = _make_usage()
        confidence = _make_confidence(0.72)
        output = format_deep_mode(sections, rows, confidence, usage)
        assert "EXECUTIVE SUMMARY" in output

    def test_contains_scenario_table(self):
        sections = self._build_sections()
        rows = run_base_downside_stress()
        usage = _make_usage()
        confidence = _make_confidence(0.72)
        output = format_deep_mode(sections, rows, confidence, usage)
        assert "Base Case" in output
        assert "Downside Case" in output
        assert "Stress Case" in output

    def test_contains_contradiction_section(self):
        sections = self._build_sections()
        rows = run_base_downside_stress()
        usage = _make_usage()
        confidence = _make_confidence(0.72)
        output = format_deep_mode(sections, rows, confidence, usage)
        assert "CONTRADICTION CHECK" in output

    def test_contains_confidence_section(self):
        sections = self._build_sections()
        rows = run_base_downside_stress()
        usage = _make_usage()
        confidence = _make_confidence(0.72)
        output = format_deep_mode(sections, rows, confidence, usage)
        assert "CONFIDENCE" in output

    def test_contains_cost_section(self):
        sections = self._build_sections()
        rows = run_base_downside_stress()
        usage = _make_usage()
        confidence = _make_confidence(0.72)
        output = format_deep_mode(sections, rows, confidence, usage)
        assert "TOKEN USAGE" in output
        assert "Estimated Cost" in output

    def test_no_emojis_in_deep_output(self):
        sections = self._build_sections()
        rows = run_base_downside_stress()
        usage = _make_usage()
        confidence = _make_confidence(0.72)
        output = format_deep_mode(sections, rows, confidence, usage)
        for emoji_char in ["🚀", "📊", "💰", "✅", "❌"]:
            assert emoji_char not in output


class TestFormatScenarioOnly:

    def test_returns_string(self):
        rows = run_base_downside_stress()
        usage = _make_usage()
        output = format_scenario_only(rows, usage, trigger="High Inflation")
        assert isinstance(output, str)

    def test_contains_trigger(self):
        rows = run_base_downside_stress()
        usage = _make_usage()
        output = format_scenario_only(rows, usage, trigger="High Inflation")
        assert "High Inflation" in output

    def test_contains_scenario_re_run_label(self):
        rows = run_base_downside_stress()
        usage = _make_usage()
        output = format_scenario_only(rows, usage)
        assert "SCENARIO RE-RUN" in output
