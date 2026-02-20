"""
tests/test_contradiction_detector.py
Unit tests for src/contradiction_detector.py
"""

import pytest
from src.contradiction_detector import detect_contradictions, format_contradiction_block


class TestDetectContradictions:

    def test_no_contradictions_empty_data(self):
        result = detect_contradictions({})
        assert result == []

    def test_no_contradictions_consistent_data(self):
        data = {
            "revenue_growth_reported": 0.12,
            "revenue_growth_guided": 0.10,  # within 5% threshold
            "operating_margin_current": 0.25,
            "operating_margin_prior": 0.22,
            "margin_improvement_claim": True,  # margins did improve
            "total_debt_current": 500.0,
            "total_debt_prior": 600.0,
            "debt_reduction_claim": True,  # debt did fall
        }
        result = detect_contradictions(data)
        assert result == []

    def test_revenue_guidance_mismatch_detected(self):
        data = {
            "revenue_growth_reported": 0.05,
            "revenue_growth_guided": 0.18,  # 13pp gap
        }
        result = detect_contradictions(data)
        assert len(result) == 1
        assert "Revenue Guidance" in result[0]["type"]

    def test_revenue_guidance_mismatch_high_severity(self):
        data = {
            "revenue_growth_reported": 0.02,
            "revenue_growth_guided": 0.20,  # 18pp gap → HIGH
        }
        result = detect_contradictions(data)
        assert result[0]["severity"] == "HIGH"

    def test_revenue_guidance_mismatch_medium_severity(self):
        data = {
            "revenue_growth_reported": 0.10,
            "revenue_growth_guided": 0.16,  # 6pp gap → MEDIUM
        }
        result = detect_contradictions(data)
        assert result[0]["severity"] == "MEDIUM"

    def test_margin_improvement_claim_vs_declining_margin(self):
        data = {
            "operating_margin_current": 0.18,
            "operating_margin_prior": 0.22,
            "margin_improvement_claim": True,
        }
        result = detect_contradictions(data)
        types = [c["type"] for c in result]
        assert any("Margin" in t for t in types)
        assert result[0]["severity"] == "HIGH"

    def test_margin_claim_not_triggered_when_false(self):
        data = {
            "operating_margin_current": 0.18,
            "operating_margin_prior": 0.22,
            "margin_improvement_claim": False,  # claim not made
        }
        result = detect_contradictions(data)
        assert result == []

    def test_debt_reduction_claim_vs_rising_debt(self):
        data = {
            "total_debt_current": 800.0,
            "total_debt_prior": 600.0,
            "debt_reduction_claim": True,
        }
        result = detect_contradictions(data)
        types = [c["type"] for c in result]
        assert any("Debt" in t for t in types)
        assert result[0]["severity"] == "HIGH"

    def test_profitability_claim_vs_declining_net_income(self):
        data = {
            "net_income_current": 200.0,
            "net_income_prior": 350.0,
            "profitability_claim": True,
        }
        result = detect_contradictions(data)
        types = [c["type"] for c in result]
        assert any("Profitability" in t for t in types)

    def test_negative_fcf_with_positive_claim(self):
        data = {
            "fcf_current": -150.0,
            "claims": ["We delivered strong free cash flow this quarter."],
        }
        result = detect_contradictions(data)
        types = [c["type"] for c in result]
        assert any("FCF" in t for t in types)
        assert result[0]["severity"] == "HIGH"

    def test_multiple_contradictions_detected(self):
        data = {
            "revenue_growth_reported": 0.03,
            "revenue_growth_guided": 0.15,
            "operating_margin_current": 0.10,
            "operating_margin_prior": 0.20,
            "margin_improvement_claim": True,
            "total_debt_current": 1000.0,
            "total_debt_prior": 700.0,
            "debt_reduction_claim": True,
        }
        result = detect_contradictions(data)
        assert len(result) >= 3

    def test_result_has_required_keys(self):
        data = {
            "revenue_growth_reported": 0.02,
            "revenue_growth_guided": 0.20,
        }
        result = detect_contradictions(data)
        assert len(result) > 0
        for item in result:
            assert "type" in item
            assert "description" in item
            assert "severity" in item


class TestFormatContradictionBlock:

    def test_empty_returns_no_contradiction_message(self):
        output = format_contradiction_block([])
        assert "No contradictions" in output

    def test_contradiction_appears_in_output(self):
        contras = [
            {"type": "Revenue Guidance Mismatch", "description": "Guided 15% but grew 3%.", "severity": "HIGH"}
        ]
        output = format_contradiction_block(contras)
        assert "Revenue Guidance Mismatch" in output
        assert "HIGH" in output
