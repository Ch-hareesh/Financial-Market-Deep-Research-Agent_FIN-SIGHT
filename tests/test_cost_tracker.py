"""
tests/test_cost_tracker.py
Unit tests for src/cost_tracker.py
"""

import pytest
from src.cost_tracker import estimate_cost, estimate_quick_mode_cost, estimate_deep_mode_cost, Timer


class TestEstimateCost:

    def test_returns_usage_summary(self):
        from src.cost_tracker import UsageSummary
        result = estimate_cost(1000, 500)
        assert isinstance(result, UsageSummary)

    def test_total_tokens_is_sum(self):
        result = estimate_cost(1000, 500)
        assert result.total_tokens == 1500

    def test_prompt_tokens_correct(self):
        result = estimate_cost(800, 200)
        assert result.prompt_tokens == 800

    def test_completion_tokens_correct(self):
        result = estimate_cost(800, 200)
        assert result.completion_tokens == 200

    def test_cost_is_non_negative(self):
        result = estimate_cost(100, 100)
        assert result.estimated_cost_usd >= 0.0

    def test_zero_tokens_zero_cost(self):
        result = estimate_cost(0, 0)
        assert result.estimated_cost_usd == 0.0
        assert result.total_tokens == 0

    def test_more_tokens_higher_cost(self):
        small = estimate_cost(100, 100)
        large = estimate_cost(10000, 10000)
        assert large.estimated_cost_usd > small.estimated_cost_usd

    def test_model_field_set(self):
        result = estimate_cost(500, 300, model="gemini-2.0-flash")
        assert result.model == "gemini-2.0-flash"

    def test_latency_ms_stored(self):
        result = estimate_cost(500, 300, latency_ms=1500)
        assert result.latency_ms == 1500

    def test_default_model_from_config(self):
        """Should use MODEL_NAME from config if model not specified."""
        from src.config import MODEL_NAME
        result = estimate_cost(100, 100)
        assert result.model == MODEL_NAME

    def test_unknown_model_uses_default_pricing(self):
        result = estimate_cost(1000, 1000, model="some-unknown-model")
        assert result.estimated_cost_usd >= 0.0  # should not crash

    def test_format_returns_string(self):
        result = estimate_cost(1000, 500)
        formatted = result.format()
        assert isinstance(formatted, str)
        assert "Prompt Tokens" in formatted
        assert "Estimated Cost" in formatted


class TestConvenienceEstimators:

    def test_quick_mode_cost(self):
        result = estimate_quick_mode_cost()
        assert result.prompt_tokens == 1200
        assert result.estimated_cost_usd >= 0.0

    def test_deep_mode_cost(self):
        result = estimate_deep_mode_cost()
        assert result.prompt_tokens == 2500
        assert result.estimated_cost_usd >= 0.0

    def test_deep_more_than_quick(self):
        quick = estimate_quick_mode_cost()
        deep = estimate_deep_mode_cost()
        assert deep.estimated_cost_usd > quick.estimated_cost_usd


class TestTimer:

    def test_context_manager_returns_timer(self):
        with Timer() as t:
            pass
        assert isinstance(t.elapsed_ms, int)

    def test_elapsed_ms_non_negative(self):
        with Timer() as t:
            pass
        assert t.elapsed_ms >= 0

    def test_elapsed_ms_greater_than_sleep(self):
        import time
        with Timer() as t:
            time.sleep(0.05)  # 50ms
        assert t.elapsed_ms >= 40  # allow jitter margin
