"""Tests for calculations_runner.py."""

import pytest

from stock_analyst.analysis.calculations_runner import run_all_calculations
from stock_analyst.data_collection.stock_directory import StockInfo
from stock_analyst.parsing.quantitative_data import RawQuantitativeData


def make_stock_info(market_cap: float) -> StockInfo:
    return StockInfo(
        ticker="NVDA",
        name="NVIDIA Corporation Common Stock",
        exchange="NASDAQ",
        sector="Technology",
        industry="Semiconductors",
        country="United States",
        market_cap=market_cap,
        ipo_year=1999,
    )


def test_valuation_ratios_from_a_first_quarter_filing_printed_in_millions():
    """End-to-end sanity check with NVDA-shaped Q1 FY2027 numbers.

    The filing prints amounts in millions; the pipeline unit-scales each
    table's parse result before run_all_calculations sees it, and
    run_all_calculations annualizes the year-to-date flows (x4 for Q1). The
    resulting valuation ratios must land in normal single-to-double-digit
    territory, not the millions seen before the unit-scale fix.
    """
    as_printed_in_millions = RawQuantitativeData(
        revenue=81615.0,
        net_income=58321.0,
    )
    unit_scaled = as_printed_in_millions.apply_unit_scale(1_000_000.0, 1_000_000.0)
    stock_info = make_stock_info(market_cap=5_422_978_000_000.0)

    calculated_metrics = run_all_calculations(
        stock_info=stock_info, parse_result=unit_scaled, fiscal_quarter="Q1"
    )

    assert calculated_metrics.price_to_sales == pytest.approx(16.6, abs=0.1)
    assert calculated_metrics.price_to_earnings == pytest.approx(23.2, abs=0.1)


def test_flow_over_flow_metrics_are_invariant_under_annualization():
    parse_result = RawQuantitativeData(
        revenue=100.0,
        net_income=20.0,
        operating_cash_flow=25.0,
    )
    stock_info = make_stock_info(market_cap=1_000.0)

    first_quarter = run_all_calculations(
        stock_info=stock_info, parse_result=parse_result, fiscal_quarter="Q1"
    )
    fourth_quarter = run_all_calculations(
        stock_info=stock_info, parse_result=parse_result, fiscal_quarter="Q4"
    )

    assert first_quarter.net_profit_margin == fourth_quarter.net_profit_margin
    assert (
        first_quarter.operating_cash_flow_to_net_income
        == fourth_quarter.operating_cash_flow_to_net_income
    )
    # ...while a flow-vs-market-cap metric annualizes: Q1 earnings count x4.
    assert first_quarter.price_to_earnings == fourth_quarter.price_to_earnings / 4.0
