"""Tests for quarterly_report_parse_result.py."""

from stock_analyst.quarterly_report_parse_result import (
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
