"""
tests/test_scenario_engine.py
Unit tests for src/scenario_engine.py
"""

import pytest
from src.scenario_engine import (
    run_scenarios,
    run_base_downside_stress,
    format_scenario_table,
    ScenarioRow,
)


class TestRunScenarios:

    def test_default_returns_three_rows(self):
        rows = run_scenarios()
        assert len(rows) == 3

    def test_inflation_scenario_resolved(self):
        rows = run_scenarios(["high_inflation"])
        assert len(rows) == 1
        assert rows[0].scenario == "High Inflation"

    def test_alias_inflation_resolved(self):
        rows = run_scenarios(["inflation"])
        assert len(rows) == 1
        assert rows[0].scenario == "High Inflation"

    def test_alias_rate_hike_resolved(self):
        rows = run_scenarios(["rate hike"])
        assert len(rows) == 1
        assert rows[0].scenario == "Interest Rate Hike"

    def test_alias_recession_resolved(self):
        rows = run_scenarios(["recession"])
        assert len(rows) == 1
        assert rows[0].scenario == "Recession / Demand Contraction"

    def test_multiple_scenarios(self):
        rows = run_scenarios(["high_inflation", "recession", "regulatory_tightening"])
        assert len(rows) == 3
        scenario_names = [r.scenario for r in rows]
        assert "High Inflation" in scenario_names
        assert "Regulatory Tightening" in scenario_names

    def test_unknown_scenario_fallback_to_default(self):
        rows = run_scenarios(["nonexistent_scenario"])
        # Falls back to default 3
        assert len(rows) == 3

    def test_empty_list_returns_default(self):
        rows = run_scenarios([])
        assert len(rows) == 3

    def test_row_has_required_fields(self):
        rows = run_scenarios(["high_inflation"])
        row = rows[0]
        assert row.scenario
        assert row.revenue_impact
        assert row.margin_impact
        assert row.valuation_impact
        assert row.risk_level

    def test_all_risk_levels_non_empty(self):
        rows = run_scenarios()
        for row in rows:
            assert row.risk_level in ("LOW", "MEDIUM", "HIGH", "VERY HIGH")


class TestRunBaseDownsideStress:

    def test_returns_three_rows(self):
        rows = run_base_downside_stress()
        assert len(rows) == 3

    def test_first_row_is_base_case(self):
        rows = run_base_downside_stress()
        assert rows[0].scenario == "Base Case"

    def test_second_row_is_downside(self):
        rows = run_base_downside_stress()
        assert rows[1].scenario == "Downside Case"

    def test_third_row_is_stress(self):
        rows = run_base_downside_stress()
        assert rows[2].scenario == "Stress Case"

    def test_base_case_lowest_risk(self):
        rows = run_base_downside_stress()
        assert rows[0].risk_level == "LOW"

    def test_stress_case_highest_risk(self):
        rows = run_base_downside_stress()
        assert rows[2].risk_level == "VERY HIGH"


class TestFormatScenarioTable:

    def test_returns_string(self):
        rows = run_base_downside_stress()
        output = format_scenario_table(rows)
        assert isinstance(output, str)

    def test_contains_header(self):
        rows = run_base_downside_stress()
        output = format_scenario_table(rows)
        assert "Scenario" in output
        assert "Revenue Impact" in output
        assert "Risk Level" in output

    def test_contains_all_scenarios(self):
        rows = run_base_downside_stress()
        output = format_scenario_table(rows)
        assert "Base Case" in output
        assert "Downside Case" in output
        assert "Stress Case" in output

    def test_empty_rows_returns_header_only(self):
        output = format_scenario_table([])
        assert "Scenario" in output
