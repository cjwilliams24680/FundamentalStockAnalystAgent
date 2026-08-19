"""Tests for interpretations.py.

Band-boundary checks assert falls_outside_normal_range on the flagging side
of each threshold. Text assertions target load-bearing phrases only (sibling
field names, "no debt") — never full-string equality — so the wording can be
polished without breaking tests.
"""

import pytest

from stock_analyst.analysis import calculations, interpretations


def test_raw_value_passes_through_unchanged():
    result = interpretations.interpret_current_ratio(1.75)
    assert result.raw_value == 1.75
    assert result.field_name == "current_ratio"


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------


def test_building_block_sign_flags():
    assert interpretations.interpret_gross_profit(-50.0).falls_outside_normal_range is True
    assert interpretations.interpret_gross_profit(400.0).falls_outside_normal_range is False
    assert (
        interpretations.interpret_earnings_before_interest_taxes_depreciation_and_amortization(
            -10.0
        ).falls_outside_normal_range
        is True
    )
    assert (
        interpretations.interpret_net_debt(-100.0).falls_outside_normal_range is True
    )  # net cash flags literally
    assert interpretations.interpret_net_debt(100.0).falls_outside_normal_range is False
    assert (
        interpretations.interpret_working_capital(-100.0).falls_outside_normal_range is False
    )  # normal for some retail
    assert interpretations.interpret_invested_capital(-5.0).falls_outside_normal_range is True
    assert interpretations.interpret_enterprise_value(-1000.0).falls_outside_normal_range is True
    assert (
        interpretations.interpret_total_debt(0.0).falls_outside_normal_range is False
    )  # debt-free, unambiguous
    assert interpretations.interpret_free_cash_flow(-25.0).falls_outside_normal_range is True


def test_effective_tax_rate_bands():
    assert interpretations.interpret_effective_tax_rate(0.01).falls_outside_normal_range is True
    assert interpretations.interpret_effective_tax_rate(0.21).falls_outside_normal_range is False
    assert interpretations.interpret_effective_tax_rate(0.45).falls_outside_normal_range is True


# ---------------------------------------------------------------------------
# Profitability
# ---------------------------------------------------------------------------


def test_margin_bands():
    assert interpretations.interpret_operating_margin(-0.05).falls_outside_normal_range is True
    assert interpretations.interpret_operating_margin(0.15).falls_outside_normal_range is False
    assert (
        interpretations.interpret_operating_margin(0.45).falls_outside_normal_range is True
    )  # too good — verify
    assert interpretations.interpret_net_profit_margin(0.08).falls_outside_normal_range is False
    assert interpretations.interpret_net_profit_margin(0.35).falls_outside_normal_range is True
    assert (
        interpretations.interpret_gross_profit_margin(0.80).falls_outside_normal_range is False
    )  # software-normal
    assert interpretations.interpret_gross_profit_margin(0.95).falls_outside_normal_range is True
    assert (
        interpretations.interpret_earnings_before_interest_taxes_depreciation_and_amortization_margin(
            0.20
        ).falls_outside_normal_range
        is False
    )


# ---------------------------------------------------------------------------
# Liquidity
# ---------------------------------------------------------------------------


def test_liquidity_bands():
    assert interpretations.interpret_current_ratio(0.8).falls_outside_normal_range is True
    assert interpretations.interpret_current_ratio(2.2).falls_outside_normal_range is False
    assert (
        interpretations.interpret_current_ratio(4.0).falls_outside_normal_range is True
    )  # lazy capital
    assert interpretations.interpret_quick_ratio(0.7).falls_outside_normal_range is True
    assert interpretations.interpret_quick_ratio(1.3).falls_outside_normal_range is False
    assert interpretations.interpret_cash_ratio(0.3).falls_outside_normal_range is False
    assert (
        interpretations.interpret_cash_ratio(1.5).falls_outside_normal_range is True
    )  # idle-cash hoard
    assert (
        interpretations.interpret_operating_cash_flow_ratio(-0.2).falls_outside_normal_range is True
    )
    assert (
        interpretations.interpret_operating_cash_flow_ratio(0.6).falls_outside_normal_range is False
    )
    assert (
        interpretations.interpret_defensive_interval_ratio(20.0).falls_outside_normal_range is True
    )
    assert (
        interpretations.interpret_defensive_interval_ratio(120.0).falls_outside_normal_range
        is False
    )


# ---------------------------------------------------------------------------
# Solvency & leverage
# ---------------------------------------------------------------------------


def test_solvency_and_leverage_bands():
    assert interpretations.interpret_debt_to_equity(0.5).falls_outside_normal_range is False
    assert interpretations.interpret_debt_to_equity(1.8).falls_outside_normal_range is True
    assert interpretations.interpret_debt_to_assets(0.3).falls_outside_normal_range is False
    assert interpretations.interpret_debt_to_assets(0.7).falls_outside_normal_range is True
    assert interpretations.interpret_debt_to_capital(0.5).falls_outside_normal_range is False
    assert interpretations.interpret_debt_to_capital(0.7).falls_outside_normal_range is True
    net_debt_to_ebitda = interpretations.interpret_net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization  # noqa: E501 -- unsplittable spelled-out identifier
    assert net_debt_to_ebitda(-0.5).falls_outside_normal_range is True  # net cash flags literally
    assert net_debt_to_ebitda(2.0).falls_outside_normal_range is False
    assert net_debt_to_ebitda(4.5).falls_outside_normal_range is True
    assert interpretations.interpret_interest_coverage(1.0).falls_outside_normal_range is True
    assert interpretations.interpret_interest_coverage(6.0).falls_outside_normal_range is False
    ebitda_coverage = interpretations.interpret_earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage  # noqa: E501 -- unsplittable spelled-out identifier
    assert ebitda_coverage(1.5).falls_outside_normal_range is True
    assert ebitda_coverage(8.0).falls_outside_normal_range is False
    assert (
        interpretations.interpret_operating_cash_flow_to_debt(0.5).falls_outside_normal_range
        is False
    )
    assert (
        interpretations.interpret_operating_cash_flow_to_debt(-0.1).falls_outside_normal_range
        is True
    )


# ---------------------------------------------------------------------------
# Cash flow - generation & quality
# ---------------------------------------------------------------------------


def test_cash_flow_bands():
    assert interpretations.interpret_free_cash_flow_margin(-0.05).falls_outside_normal_range is True
    assert interpretations.interpret_free_cash_flow_margin(0.12).falls_outside_normal_range is False
    assert (
        interpretations.interpret_operating_cash_flow_to_net_income(0.7).falls_outside_normal_range
        is True
    )
    assert (
        interpretations.interpret_operating_cash_flow_to_net_income(1.3).falls_outside_normal_range
        is False
    )
    assert interpretations.interpret_sloan_accruals_ratio(0.05).falls_outside_normal_range is False
    assert interpretations.interpret_sloan_accruals_ratio(0.30).falls_outside_normal_range is True
    assert interpretations.interpret_sloan_accruals_ratio(-0.20).falls_outside_normal_range is True
    assert (
        interpretations.interpret_free_cash_flow_conversion(0.9).falls_outside_normal_range is False
    )
    assert (
        interpretations.interpret_free_cash_flow_conversion(1.4).falls_outside_normal_range is True
    )  # temporary benefit
    assert (
        interpretations.interpret_capital_expenditure_intensity(0.03).falls_outside_normal_range
        is False
    )
    assert (
        interpretations.interpret_capital_expenditure_intensity(0.20).falls_outside_normal_range
        is True
    )
    assert (
        interpretations.interpret_capital_expenditures_to_depreciation(
            0.6
        ).falls_outside_normal_range
        is True
    )
    assert (
        interpretations.interpret_capital_expenditures_to_depreciation(
            1.2
        ).falls_outside_normal_range
        is False
    )


# ---------------------------------------------------------------------------
# Growth
# ---------------------------------------------------------------------------


def test_retention_rate_bands():
    assert (
        interpretations.interpret_retention_rate(-0.1).falls_outside_normal_range is True
    )  # payout above earnings
    assert interpretations.interpret_retention_rate(0.5).falls_outside_normal_range is False
    assert interpretations.interpret_retention_rate(1.0).falls_outside_normal_range is False


# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------


def test_valuation_bands():
    assert interpretations.interpret_price_to_earnings(8.0).falls_outside_normal_range is True
    assert interpretations.interpret_price_to_earnings(17.0).falls_outside_normal_range is False
    assert interpretations.interpret_price_to_earnings(60.0).falls_outside_normal_range is True
    assert interpretations.interpret_earnings_yield(-0.02).falls_outside_normal_range is True
    assert interpretations.interpret_earnings_yield(0.05).falls_outside_normal_range is False
    assert (
        interpretations.interpret_earnings_before_interest_and_taxes_to_enterprise_value(
            0.12
        ).falls_outside_normal_range
        is True
    )  # Greenblatt-cheap flags literally
    assert interpretations.interpret_price_to_book(0.8).falls_outside_normal_range is True
    assert interpretations.interpret_price_to_book(2.5).falls_outside_normal_range is False
    assert interpretations.interpret_price_to_sales(1.5).falls_outside_normal_range is False
    assert interpretations.interpret_price_to_sales(12.0).falls_outside_normal_range is True
    enterprise_value_to_ebitda = interpretations.interpret_enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization  # noqa: E501 -- unsplittable spelled-out identifier
    assert enterprise_value_to_ebitda(10.0).falls_outside_normal_range is False
    assert enterprise_value_to_ebitda(4.0).falls_outside_normal_range is True
    assert enterprise_value_to_ebitda(18.0).falls_outside_normal_range is True
    assert (
        interpretations.interpret_enterprise_value_to_earnings_before_interest_and_taxes(
            12.0
        ).falls_outside_normal_range
        is False
    )
    assert (
        interpretations.interpret_enterprise_value_to_sales(2.0).falls_outside_normal_range is False
    )
    assert (
        interpretations.interpret_enterprise_value_to_sales(11.0).falls_outside_normal_range is True
    )
    assert interpretations.interpret_free_cash_flow_yield(0.05).falls_outside_normal_range is False
    assert interpretations.interpret_free_cash_flow_yield(0.01).falls_outside_normal_range is True
    assert interpretations.interpret_free_cash_flow_yield(0.10).falls_outside_normal_range is True
    assert (
        interpretations.interpret_dividend_yield(0.0).falls_outside_normal_range is False
    )  # no dividend, uninformative
    assert interpretations.interpret_dividend_yield(0.03).falls_outside_normal_range is False
    assert (
        interpretations.interpret_dividend_yield(0.09).falls_outside_normal_range is True
    )  # pricing a cut
    assert interpretations.interpret_payout_ratio(0.45).falls_outside_normal_range is False
    assert interpretations.interpret_payout_ratio(1.2).falls_outside_normal_range is True
    assert (
        interpretations.interpret_shareholder_yield(-0.01).falls_outside_normal_range is True
    )  # net issuer
    assert interpretations.interpret_shareholder_yield(0.03).falls_outside_normal_range is False


# ---------------------------------------------------------------------------
# None handling — the three flavors
# ---------------------------------------------------------------------------


def test_none_that_means_no_debt_is_good_news():
    result = interpretations.interpret_interest_coverage(None)
    assert "no debt" in result.interpretation
    assert result.falls_outside_normal_range is False
    result = interpretations.interpret_operating_cash_flow_to_debt(None)
    assert "debt-free" in result.interpretation
    assert result.falls_outside_normal_range is False


def test_none_that_points_at_sibling_metric():
    assert "earnings_yield" in interpretations.interpret_price_to_earnings(None).interpretation
    assert "debt_to_capital" in interpretations.interpret_debt_to_equity(None).interpretation
    assert (
        "sloan_accruals_ratio"
        in interpretations.interpret_operating_cash_flow_to_net_income(None).interpretation
    )
    assert (
        "enterprise_value_to_sales"
        in interpretations.interpret_enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization(  # noqa: E501 -- unsplittable spelled-out identifier
            None
        ).interpretation
    )


# ---------------------------------------------------------------------------
# Composite scores
# ---------------------------------------------------------------------------


def test_altman_score_bands():
    assert interpretations.interpret_altman_z_score(1.0).falls_outside_normal_range is True
    assert (
        interpretations.interpret_altman_z_score(2.5).falls_outside_normal_range is True
    )  # grey zone flags
    assert interpretations.interpret_altman_z_score(3.5).falls_outside_normal_range is False
    assert interpretations.interpret_altman_z_double_prime(0.5).falls_outside_normal_range is True
    assert interpretations.interpret_altman_z_double_prime(2.0).falls_outside_normal_range is True
    assert interpretations.interpret_altman_z_double_prime(3.0).falls_outside_normal_range is False


def test_altman_zone_labels():
    for interpret_zone in (
        interpretations.interpret_altman_z_zone,
        interpretations.interpret_altman_z_double_prime_zone,
    ):
        assert interpret_zone(calculations.Z_SAFE).falls_outside_normal_range is False
        assert interpret_zone(calculations.Z_GREY).falls_outside_normal_range is True
        assert interpret_zone(calculations.Z_DISTRESS).falls_outside_normal_range is True
        assert interpret_zone(None).falls_outside_normal_range is False


def test_altman_zone_rejects_unknown_label():
    with pytest.raises(ValueError):
        interpretations.interpret_altman_z_zone("purple")
    with pytest.raises(ValueError):
        interpretations.interpret_altman_z_double_prime_zone("purple")
