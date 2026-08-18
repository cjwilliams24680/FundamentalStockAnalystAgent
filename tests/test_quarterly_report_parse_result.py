"""Tests for quarterly_report_parse_result.py."""

import pytest

from stock_analyst.quarterly_report_parse_result import (
    BALANCE_SHEET_FIELD_NAMES,
    SHARE_COUNT_FIELD_NAMES,
    YEAR_TO_DATE_FLOW_FIELD_NAMES,
    QuarterlyReportParseResult,
    count_populated_fields,
    get_diffs,
)


def test_merge_prefers_first_instance_and_falls_back_to_second():
    first = QuarterlyReportParseResult(
        revenue=100.0,
        total_assets=500.0,
    )
    second = QuarterlyReportParseResult(
        revenue=200.0,
        net_income=50.0,
        inventory=30.0,
    )

    merged = first.merge(second)

    assert merged.revenue == 100.0  # first wins when both are set
    assert merged.total_assets == 500.0  # only first has a value
    assert merged.net_income == 50.0  # falls back to second
    assert merged.inventory == 30.0
    assert merged.payables is None  # unset in both stays None


def test_merge_returns_new_instance_and_leaves_inputs_unchanged():
    first = QuarterlyReportParseResult(revenue=100.0)
    second = QuarterlyReportParseResult(net_income=50.0)

    merged = first.merge(second)

    assert merged is not first and merged is not second
    assert first.net_income is None
    assert second.revenue is None


def test_merge_covers_every_field():
    filled = QuarterlyReportParseResult(
        **{field_name: 1.0 for field_name in QuarterlyReportParseResult.model_fields}
    )
    empty = QuarterlyReportParseResult()

    assert empty.merge(filled) == filled
    assert filled.merge(empty) == filled


def test_apply_unit_scale_multiplies_monetary_and_share_fields_separately():
    parse_result = QuarterlyReportParseResult(
        revenue=81615.0,
        weighted_average_diluted_shares=24391.0,
    )

    scaled = parse_result.apply_unit_scale(1_000_000.0, 1_000_000.0)
    assert scaled.revenue == 81_615_000_000.0
    assert scaled.weighted_average_diluted_shares == 24_391_000_000.0

    scaled_with_raw_share_counts = parse_result.apply_unit_scale(1_000_000.0, 1.0)
    assert scaled_with_raw_share_counts.revenue == 81_615_000_000.0
    assert scaled_with_raw_share_counts.weighted_average_diluted_shares == 24391.0


def test_apply_unit_scale_propagates_none_and_preserves_signs():
    parse_result = QuarterlyReportParseResult(investing_cash_flow=-26429.0)

    scaled = parse_result.apply_unit_scale(1_000_000.0, 1_000_000.0)

    assert scaled.investing_cash_flow == -26_429_000_000.0
    assert scaled.revenue is None


def test_apply_unit_scale_touches_every_field():
    filled = QuarterlyReportParseResult(
        **{field_name: 1.0 for field_name in QuarterlyReportParseResult.model_fields}
    )

    scaled = filled.apply_unit_scale(1_000.0, 1_000.0)

    assert scaled is not filled
    for field_name in QuarterlyReportParseResult.model_fields:
        assert getattr(scaled, field_name) == 1_000.0


def test_annualize_year_to_date_flow_values_scales_only_flows():
    parse_result = QuarterlyReportParseResult(
        revenue=100.0,  # flow
        operating_cash_flow=40.0,  # flow
        total_assets=500.0,  # balance sheet
        weighted_average_diluted_shares=10.0,  # period average, not a flow
    )

    annualized = parse_result.annualize_year_to_date_flow_values("Q1")

    assert annualized.revenue == 400.0
    assert annualized.operating_cash_flow == 160.0
    assert annualized.total_assets == 500.0
    assert annualized.weighted_average_diluted_shares == 10.0
    assert annualized.net_income is None  # None propagates


def test_annualize_year_to_date_flow_values_factor_per_quarter():
    parse_result = QuarterlyReportParseResult(revenue=120.0)

    assert parse_result.annualize_year_to_date_flow_values("Q1").revenue == 480.0
    assert parse_result.annualize_year_to_date_flow_values("Q2").revenue == 240.0
    assert parse_result.annualize_year_to_date_flow_values("Q3").revenue == 160.0
    assert parse_result.annualize_year_to_date_flow_values("Q4").revenue == 120.0


def test_annualize_year_to_date_flow_values_rejects_unknown_quarter():
    with pytest.raises(ValueError):
        QuarterlyReportParseResult().annualize_year_to_date_flow_values("Q5")


def test_field_classification_partitions_the_model_exactly():
    all_field_names = set(QuarterlyReportParseResult.model_fields)

    union_of_classified_fields = (
        YEAR_TO_DATE_FLOW_FIELD_NAMES | BALANCE_SHEET_FIELD_NAMES | SHARE_COUNT_FIELD_NAMES
    )
    assert union_of_classified_fields == all_field_names
    assert not YEAR_TO_DATE_FLOW_FIELD_NAMES & BALANCE_SHEET_FIELD_NAMES
    assert not YEAR_TO_DATE_FLOW_FIELD_NAMES & SHARE_COUNT_FIELD_NAMES
    assert not BALANCE_SHEET_FIELD_NAMES & SHARE_COUNT_FIELD_NAMES


def test_count_populated_fields():
    assert count_populated_fields(QuarterlyReportParseResult()) == 0

    partially_filled = QuarterlyReportParseResult(
        revenue=100.0,
        net_income=0.0,  # zero is a reported value, not a gap
        inventory=30.0,
    )
    assert count_populated_fields(partially_filled) == 3

    fully_filled = QuarterlyReportParseResult(
        **{field_name: 1.0 for field_name in QuarterlyReportParseResult.model_fields}
    )
    assert count_populated_fields(fully_filled) == len(QuarterlyReportParseResult.model_fields)


def test_get_diffs():
    first = QuarterlyReportParseResult(
        revenue=100.0,  # differs
        net_income=50.0,  # equal in both
        inventory=30.0,  # set only in first
    )
    second = QuarterlyReportParseResult(
        revenue=200.0,
        net_income=50.0,
        total_assets=500.0,  # set only in second
    )

    diffs = get_diffs(first, second)

    assert diffs == [
        "revenue: 100.0 != 200.0",
        "inventory: 30.0 != None",
        "total_assets: None != 500.0",
    ]


def test_get_diffs_returns_empty_list_for_equal_instances():
    first = QuarterlyReportParseResult(revenue=100.0, net_income=50.0)
    second = QuarterlyReportParseResult(revenue=100.0, net_income=50.0)

    assert get_diffs(first, second) == []
    assert get_diffs(QuarterlyReportParseResult(), QuarterlyReportParseResult()) == []
