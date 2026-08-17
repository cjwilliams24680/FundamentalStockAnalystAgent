"""Tests for metrics.py.

Expected values are hand-computed from a single coherent fake company:
revenue 1000, cost of goods sold 600, operating income 200, pretax income 160,
net income 120, depreciation and amortization 50, operating cash flow 300,
capital expenditures 80, investing cash flow -100, cash 200 (of which
short-term investments 50), receivables 150, inventory 100, payables 120,
current assets 500, current liabilities 250, total assets 2000 (average 2000),
total debt 400, equity 1000 (average 1000), market capitalization 5000,
dividends 36, buybacks 50, issuance 10.
"""

import pytest

from stock_analyst import metrics as m

approx = pytest.approx


# ---------------------------------------------------------------------------
# Helpers & building blocks
# ---------------------------------------------------------------------------


def test_average():
    assert m.average(900, 1100) == 1000
    assert m.average(None, 1100) is None


def test_building_blocks():
    assert m.gross_profit(1000, 600) == 400
    assert m.earnings_before_interest_taxes_depreciation_and_amortization(200, 50) == 250
    assert m.effective_tax_rate(40, 160) == approx(0.25)
    assert m.effective_tax_rate(40, 0) is None
    assert m.net_operating_profit_after_tax(200, 0.25) == approx(150)
    assert m.total_debt(100, 250, 50) == 400
    assert m.net_debt(400, 150, 50) == 200
    assert m.working_capital(500, 250) == 250
    assert m.invested_capital(400, 1000, 200) == 1200
    assert m.earnings_per_share(120, 40, preferred_dividends=20) == approx(2.5)
    assert m.enterprise_value(5000, 400, 200) == 5200
    assert m.free_cash_flow(300, 80) == 220


# ---------------------------------------------------------------------------
# Profitability
# ---------------------------------------------------------------------------


def test_margins():
    assert m.gross_profit_margin(400, 1000) == approx(0.4)
    assert m.operating_margin(200, 1000) == approx(0.2)
    assert m.net_profit_margin(120, 1000) == approx(0.12)
    assert m.earnings_before_interest_taxes_depreciation_and_amortization_margin(
        250, 1000
    ) == approx(0.25)
    assert m.net_profit_margin(120, 0) is None
    assert m.net_profit_margin(None, 1000) is None


def test_returns_on_capital():
    assert m.return_on_equity(120, 1000) == approx(0.12)
    assert m.return_on_equity(120, -50) is None  # negative book equity
    assert m.return_on_assets(120, 2000) == approx(0.06)
    assert m.return_on_invested_capital(150, 1200) == approx(0.125)
    assert m.return_on_invested_capital(150, 0) is None


# ---------------------------------------------------------------------------
# Efficiency
# ---------------------------------------------------------------------------


def test_turnover_and_days():
    assert m.total_asset_turnover(1000, 2000) == approx(0.5)
    assert m.fixed_asset_turnover(1000, 400) == approx(2.5)
    assert m.working_capital_turnover(1000, 250) == approx(4.0)
    assert m.working_capital_turnover(1000, -10) is None  # CFA: uninterpretable
    assert m.days_inventory_on_hand(600, 100) == approx(365 / 6)
    assert m.days_sales_outstanding(1000, 150) == approx(365 * 0.15)
    assert m.purchases(600, 20) == 620
    assert m.days_payables_outstanding(620, 120) == approx(365 / (620 / 120))
    assert m.cash_conversion_cycle(60, 30, 40) == approx(50)
    assert m.cash_conversion_cycle(60, None, 40) is None


# ---------------------------------------------------------------------------
# Liquidity
# ---------------------------------------------------------------------------


def test_liquidity():
    assert m.current_ratio(500, 250) == approx(2.0)
    assert m.current_ratio(500, 0) is None
    assert m.quick_ratio(150, 50, 150, 250) == approx(1.4)
    assert m.cash_ratio(150, 50, 250) == approx(0.8)
    assert m.operating_cash_flow_ratio(300, 250) == approx(1.2)
    # liquid assets 300; daily spend (730 - 365) / 365 = 1/day -> 300 days
    assert m.defensive_interval_ratio(200, 50, 50, 730, 365) == approx(300)
    assert m.defensive_interval_ratio(200, 50, 50, 365, 365) is None


# ---------------------------------------------------------------------------
# Solvency & leverage
# ---------------------------------------------------------------------------


def test_leverage_ratios():
    assert m.debt_to_equity(400, 1000) == approx(0.4)
    assert m.debt_to_equity(400, -100) is None  # negative equity
    assert m.debt_to_assets(400, 2000) == approx(0.2)
    assert m.debt_to_capital(400, 1000) == approx(400 / 1400)
    assert m.debt_to_capital(400, -500) is None
    assert m.financial_leverage(2000, 1000) == approx(2.0)


def test_coverage_ratios():
    net_debt_to_earnings = (
        m.net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization
    )
    assert net_debt_to_earnings(200, 250) == approx(0.8)
    assert net_debt_to_earnings(-100, 250) == approx(-0.4)  # net cash
    assert net_debt_to_earnings(200, -50) is None
    assert m.interest_coverage(200, 25) == approx(8.0)
    assert m.interest_coverage(200, 0) is None  # no debt -> not meaningful
    assert m.earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage(
        250, 25
    ) == approx(10.0)
    assert m.operating_cash_flow_to_debt(300, 400) == approx(0.75)


# ---------------------------------------------------------------------------
# Cash flow
# ---------------------------------------------------------------------------


def test_cash_flow_metrics():
    assert m.free_cash_flow_margin(220, 1000) == approx(0.22)
    assert m.operating_cash_flow_to_net_income(300, 120) == approx(2.5)
    assert m.operating_cash_flow_to_net_income(300, 0) is None
    assert m.sloan_accruals_ratio(120, 300, -100, 2000) == approx(-0.04)
    assert m.free_cash_flow_conversion(220, 250) == approx(0.88)
    assert m.capital_expenditure_intensity(80, 1000) == approx(0.08)
    assert m.capital_expenditures_to_depreciation(80, 50) == approx(1.6)


# ---------------------------------------------------------------------------
# Growth
# ---------------------------------------------------------------------------


def test_growth():
    assert m.growth_rate(1100, 1000) == approx(0.1)
    assert m.growth_rate(1100, -50) is None  # non-positive base
    assert m.compound_annual_growth_rate(1210, 1000, 2) == approx(0.1)
    assert m.compound_annual_growth_rate(1210, 0, 2) is None
    assert m.retention_rate(0.3) == approx(0.7)
    assert m.sustainable_growth_rate(0.12, 0.3) == approx(0.084)
    # (capital expenditures 80 - depreciation 50 + working capital change 30)
    # / net operating profit after tax 150
    assert m.reinvestment_rate(80, 50, 30, 150) == approx(0.4)
    assert m.reinvestment_rate(80, 50, 30, -10) is None
    assert m.fundamental_growth(0.4, 0.125) == approx(0.05)


# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------


def test_price_multiples():
    assert m.price_to_earnings(5000, 120) == approx(5000 / 120)
    assert m.price_to_earnings(5000, -5) is None  # undefined on losses
    assert m.earnings_yield(120, 5000) == approx(0.024)
    assert m.earnings_yield(-5, 5000) == approx(-0.001)  # defined on losses
    assert m.earnings_before_interest_and_taxes_to_enterprise_value(200, 5200) == approx(200 / 5200)
    assert m.price_to_book(5000, 1000) == approx(5.0)
    assert m.price_to_book(5000, -100) is None
    assert m.price_to_sales(5000, 1000) == approx(5.0)


def test_enterprise_value_multiples():
    enterprise_value_to_earnings = (
        m.enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization
    )
    assert enterprise_value_to_earnings(5200, 250) == approx(20.8)
    assert enterprise_value_to_earnings(5200, -10) is None
    assert m.enterprise_value_to_earnings_before_interest_and_taxes(5200, 200) == approx(26.0)
    assert m.enterprise_value_to_sales(5200, 1000) == approx(5.2)


def test_yields_and_payout():
    assert m.free_cash_flow_yield(220, 5000) == approx(0.044)
    assert m.dividend_yield(36, 5000) == approx(0.0072)
    assert m.payout_ratio(36, 120) == approx(0.3)
    assert m.payout_ratio(36, -10) is None
    assert m.shareholder_yield(36, 50, 10, 5000) == approx(0.0152)


# ---------------------------------------------------------------------------
# Composite: Piotroski F-Score
# ---------------------------------------------------------------------------

STRONG_YEAR = dict(
    net_income=120,
    net_income_prior=80,
    operating_cash_flow=300,
    beginning_total_assets=2000,
    beginning_total_assets_prior=2000,
    long_term_debt=250,
    long_term_debt_prior=300,
    average_total_assets=2000,
    average_total_assets_prior=2000,
    current_assets=500,
    current_liabilities=250,
    current_assets_prior=450,
    current_liabilities_prior=250,
    revenue=1000,
    revenue_prior=900,
    cost_of_goods_sold=600,
    cost_of_goods_sold_prior=560,  # prior margin 340/900 = 0.378 < 0.4
    common_stock_issued=0,
)


def test_f_score_all_signals_pass():
    result = m.piotroski_f_score(**STRONG_YEAR)
    assert result.score == 9
    assert result.max_score == 9
    assert all(value is True for value in result.signals.values())


def test_f_score_partial_data():
    inputs = STRONG_YEAR | dict(common_stock_issued=None, cost_of_goods_sold_prior=None)
    result = m.piotroski_f_score(**inputs)
    assert result.max_score == 7  # issuance + gross-margin signals unevaluable
    assert result.score == 7
    assert result.signals["no_stock_issuance"] is None
    assert result.signals["improving_gross_margin"] is None


def test_f_score_failing_signals():
    inputs = STRONG_YEAR | dict(
        net_income=-50,  # fails the two return-on-assets signals
        common_stock_issued=25,  # fails no_stock_issuance
    )
    result = m.piotroski_f_score(**inputs)
    assert result.signals["positive_return_on_assets"] is False
    assert result.signals["improving_return_on_assets"] is False
    assert result.signals["no_stock_issuance"] is False
    assert result.signals["operating_cash_flow_exceeds_net_income"] is True
    assert result.score == 6


# ---------------------------------------------------------------------------
# Composite: Altman Z-Score
# ---------------------------------------------------------------------------


def test_altman_z_score():
    # X1=0.125, X2=0.25, X3=0.1, X4=5, X5=0.5
    # Z = 1.2(.125) + 1.4(.25) + 3.3(.1) + 0.6(5) + 1.0(.5) = 4.33
    z_score = m.altman_z_score(
        working_capital=250,
        retained_earnings=500,
        earnings_before_interest_and_taxes=200,
        market_capitalization=5000,
        total_liabilities=1000,
        revenue=1000,
        total_assets=2000,
    )
    assert z_score == approx(4.33)
    assert m.altman_z_zone(z_score) == m.Z_SAFE
    assert m.altman_z_zone(2.0) == m.Z_GREY
    assert m.altman_z_zone(1.5) == m.Z_DISTRESS
    assert m.altman_z_zone(None) is None


def test_altman_z_double_prime():
    # X1=0.125, X2=0.25, X3=0.1, X4'=1.0
    # Z'' = 6.56(.125) + 3.26(.25) + 6.72(.1) + 1.05(1.0) = 3.357
    z_score = m.altman_z_double_prime(
        working_capital=250,
        retained_earnings=500,
        earnings_before_interest_and_taxes=200,
        book_equity=1000,
        total_liabilities=1000,
        total_assets=2000,
    )
    assert z_score == approx(3.357)
    assert m.altman_z_double_prime_zone(z_score) == m.Z_SAFE
    assert m.altman_z_double_prime_zone(2.0) == m.Z_GREY
    assert m.altman_z_double_prime_zone(1.0) == m.Z_DISTRESS


# ---------------------------------------------------------------------------
# Composite: DuPont
# ---------------------------------------------------------------------------


def test_dupont_three_factor():
    result = m.dupont_three_factor(
        net_income=120, revenue=1000, average_total_assets=2000, average_total_equity=1000
    )
    assert result.net_margin == approx(0.12)
    assert result.asset_turnover == approx(0.5)
    assert result.equity_multiplier == approx(2.0)
    assert result.return_on_equity == approx(0.12)  # ties out with the direct ratio
    assert result.return_on_equity == approx(m.return_on_equity(120, 1000))


def test_dupont_five_factor():
    result = m.dupont_five_factor(
        net_income=120,
        pretax_income=160,
        earnings_before_interest_and_taxes=200,
        revenue=1000,
        average_total_assets=2000,
        average_total_equity=1000,
    )
    assert result.tax_burden == approx(0.75)
    assert result.interest_burden == approx(0.8)
    assert result.operating_income_margin == approx(0.2)
    assert result.return_on_equity == approx(0.12)  # 0.75 * 0.8 * 0.2 * 0.5 * 2
    assert m.dupont_five_factor(
        net_income=120,
        pretax_income=-10,
        earnings_before_interest_and_taxes=200,
        revenue=1000,
        average_total_assets=2000,
        average_total_equity=1000,
    ) is None


# ---------------------------------------------------------------------------
# Composite: Beneish M-Score
# ---------------------------------------------------------------------------

STEADY_PERIOD = m.BeneishPeriod(
    revenue=1000,
    cost_of_goods_sold=600,
    receivables=100,
    current_assets=500,
    net_property_plant_and_equipment=400,
    total_assets=2000,
    depreciation=50,
    selling_general_and_administrative_expense=100,
    long_term_debt=300,
    current_liabilities=250,
    income_from_continuing_operations=120,
    operating_cash_flow=300,
)


def test_beneish_steady_state():
    # Identical periods -> all seven indices are exactly 1;
    # total accruals = (120 - 300) / 2000
    result = m.beneish_m_score(STEADY_PERIOD, STEADY_PERIOD)
    for name in (
        "days_sales_in_receivables_index",
        "gross_margin_index",
        "asset_quality_index",
        "sales_growth_index",
        "depreciation_index",
        "selling_general_and_administrative_index",
        "leverage_index",
    ):
        assert result.indices[name] == approx(1.0)
    assert result.indices["total_accruals_to_total_assets"] == approx(-0.09)
    # M = -4.840 + (0.920+0.528+0.404+0.892+0.115-0.172-0.327) + 4.679*(-0.09)
    assert result.m_score == approx(-4.840 + 2.360 + 4.679 * -0.09)
    assert result.likely_manipulator is False


def test_beneish_flags_aggressive_accruals():
    # Same company but earnings far ahead of cash flow and ballooning receivables
    aggressive = m.BeneishPeriod(
        revenue=1400,  # sales growth index 1.4
        cost_of_goods_sold=900,
        receivables=350,  # receivable-days index (350/1400)/(100/1000) = 2.5
        current_assets=800,
        net_property_plant_and_equipment=400,
        total_assets=2400,
        depreciation=50,
        selling_general_and_administrative_expense=110,
        long_term_debt=300,
        current_liabilities=300,
        income_from_continuing_operations=250,
        operating_cash_flow=-50,  # total accruals = 300/2400 = 0.125
    )
    result = m.beneish_m_score(aggressive, STEADY_PERIOD)
    assert result.likely_manipulator is True


def test_beneish_uncomputable_returns_none():
    zero_revenue_prior = m.BeneishPeriod(
        revenue=0,
        cost_of_goods_sold=0,
        receivables=0,
        current_assets=500,
        net_property_plant_and_equipment=400,
        total_assets=2000,
        depreciation=50,
        selling_general_and_administrative_expense=100,
        long_term_debt=300,
        current_liabilities=250,
        income_from_continuing_operations=0,
        operating_cash_flow=0,
    )
    assert m.beneish_m_score(STEADY_PERIOD, zero_revenue_prior) is None
