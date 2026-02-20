"""
tests/test_confidence_engine.py
Unit tests for src/confidence_engine.py
"""

import pytest
from src.confidence_engine import calculate_confidence, format_confidence_block


class TestCalculateConfidence:

    def test_perfect_conditions_high_score(self):
        result = calculate_confidence(
            data_completeness=1.0,
            contradictions=[],
            source_count=3,
            guidance_verified=True,
        )
        assert result.score >= 0.75
        assert result.grade == "HIGH"

    def test_score_in_valid_range(self):
        result = calculate_confidence(
            data_completeness=0.5,
            contradictions=[{"type": "Test", "severity": "HIGH"}],
            source_count=1,
            guidance_verified=False,
        )
        assert 0.0 <= result.score <= 1.0

    def test_contradiction_reduces_score(self):
        no_contra = calculate_confidence(1.0, [], 3, True)
        with_contra = calculate_confidence(
            1.0,
            [{"type": "X", "description": "Y", "severity": "MEDIUM"}],
            3,
            True,
        )
        assert with_contra.score < no_contra.score

    def test_high_severity_contradiction_greater_penalty(self):
        medium = calculate_confidence(
            1.0,
            [{"type": "X", "description": "Y", "severity": "MEDIUM"}],
            3,
            True,
        )
        high = calculate_confidence(
            1.0,
            [{"type": "X", "description": "Y", "severity": "HIGH"}],
            3,
            True,
        )
        assert high.score <= medium.score

    def test_missing_data_reduces_score(self):
        full = calculate_confidence(1.0, [], 3, True)
        partial = calculate_confidence(0.25, [], 3, True)
        assert partial.score < full.score

    def test_single_source_reduces_score(self):
        multi = calculate_confidence(1.0, [], 3, True)
        single = calculate_confidence(1.0, [], 1, True)
        assert single.score < multi.score

    def test_unverified_guidance_reduces_score(self):
        verified = calculate_confidence(1.0, [], 3, True)
        unverified = calculate_confidence(1.0, [], 3, False)
        assert unverified.score < verified.score

    def test_score_floor_applied(self):
        result = calculate_confidence(
            data_completeness=0.0,
            contradictions=[
                {"type": "A", "description": "B", "severity": "HIGH"},
                {"type": "C", "description": "D", "severity": "HIGH"},
                {"type": "E", "description": "F", "severity": "HIGH"},
            ],
            source_count=1,
            guidance_verified=False,
        )
        assert result.score >= 0.10  # floor

    def test_grade_low_for_low_score(self):
        result = calculate_confidence(
            data_completeness=0.0,
            contradictions=[{"type": "X", "description": "Y", "severity": "HIGH"}],
            source_count=1,
            guidance_verified=False,
        )
        assert result.grade in ("LOW", "MEDIUM")  # account for floor

    def test_deductions_list_populated(self):
        result = calculate_confidence(0.5, [], 1, False)
        assert isinstance(result.deductions, list)
        assert len(result.deductions) > 0

    def test_rationale_is_string(self):
        result = calculate_confidence(0.8, [], 2, True)
        assert isinstance(result.rationale, str)
        assert len(result.rationale) > 0


class TestFormatConfidenceBlock:

    def test_returns_string(self):
        from src.confidence_engine import ConfidenceResult
        r = ConfidenceResult(score=0.72, grade="MEDIUM", rationale="Test rationale.", deductions=["reason a"])
        output = format_confidence_block(r)
        assert isinstance(output, str)

    def test_contains_score(self):
        from src.confidence_engine import ConfidenceResult
        r = ConfidenceResult(score=0.80, grade="HIGH", rationale="Good data.", deductions=[])
        output = format_confidence_block(r)
        assert "0.80" in output

    def test_contains_grade(self):
        from src.confidence_engine import ConfidenceResult
        r = ConfidenceResult(score=0.45, grade="LOW", rationale="Missing data.", deductions=["Missing revenue"])
        output = format_confidence_block(r)
        assert "LOW" in output
