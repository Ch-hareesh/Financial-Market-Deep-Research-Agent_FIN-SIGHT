"""
tests/test_mode_classifier.py
Unit tests for src/mode_classifier.py
"""

import pytest
from src.mode_classifier import classify_mode, explain_classification


class TestClassifyMode:

    # --- QUICK MODE triggers ---

    def test_short_single_metric_query(self):
        assert classify_mode("What is Apple's revenue?") == "QUICK"

    def test_summarize_keyword(self):
        assert classify_mode("Summarize last quarter earnings.") == "QUICK"

    def test_recap_keyword(self):
        assert classify_mode("Earnings recap for MSFT Q3.") == "QUICK"

    def test_brief_snapshot(self):
        assert classify_mode("Give me a quick snapshot of Tesla.") == "QUICK"

    def test_empty_query(self):
        assert classify_mode("") == "QUICK"

    def test_whitespace_query(self):
        assert classify_mode("   ") == "QUICK"

    def test_short_word_count(self):
        # 5 words, no deep keywords
        assert classify_mode("What is the net profit?") == "QUICK"

    # --- DEEP MODE triggers ---

    def test_compare_keyword(self):
        assert classify_mode("Compare Apple and Microsoft performance.") == "DEEP"

    def test_bull_bear_keyword(self):
        assert classify_mode("Generate bull and bear case for NVDA.") == "DEEP"

    def test_scenario_keyword(self):
        assert classify_mode("Run scenario analysis for inflation impact.") == "DEEP"

    def test_sensitivity_keyword(self):
        assert classify_mode("Sensitivity analysis on revenue assumptions.") == "DEEP"

    def test_valuation_keyword(self):
        assert classify_mode("Valuation analysis using DCF and peer multiples.") == "DEEP"

    def test_versus_keyword(self):
        assert classify_mode("Amazon versus Flipkart market comparison.") == "DEEP"

    def test_full_fundamental_breakdown(self):
        assert classify_mode("Full fundamental breakdown for Reliance Industries.") == "DEEP"

    def test_investment_thesis(self):
        assert classify_mode("What is the investment thesis for Tesla?") == "DEEP"

    def test_deep_keyword_overrides_short_length(self):
        # Short query but contains a deep keyword — should be DEEP
        assert classify_mode("Compare AAPL vs GOOG.") == "DEEP"


class TestExplainClassification:

    def test_returns_dict_with_mode(self):
        result = explain_classification("Summarize revenue growth.")
        assert "mode" in result
        assert result["mode"] in ("QUICK", "DEEP")

    def test_deep_reason_mentions_keyword(self):
        result = explain_classification("Compare Apple and Google.")
        assert result["mode"] == "DEEP"
        assert "compare" in result["reason"].lower()

    def test_quick_reason_mentions_keyword(self):
        result = explain_classification("Summarize last quarter.")
        assert result["mode"] == "QUICK"
        assert "summarize" in result["reason"].lower()

    def test_word_count_returned(self):
        result = explain_classification("What is ROE?")
        assert "query_word_count" in result
        assert isinstance(result["query_word_count"], int)
