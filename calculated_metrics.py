"""Calculated results produced by the functions in :mod:`metrics` — the
output counterpart to :class:`quarterly_report_parse_result.QuarterlyReportParseResult`.

:class:`CalculatedMetrics` holds one field per calculation in ``metrics.py``,
grouped under the same section banners so the class reads as a table of
contents for that module. Conventions carry over from ``metrics.py``:

- Ratios are decimal fractions (0.25 == 25%); day-count metrics are days;
  building blocks (gross profit, total debt, enterprise value, ...) are
  absolute amounts in the filing's currency, except ``earnings_per_share``.
- Every field defaults to ``None``, meaning the metric was not computable for
  the given inputs (missing data, zero denominator, or not meaningful per the
  reference doc).
- The four ``..._growth`` fields are year-over-year applications of
  :func:`metrics.growth_rate` to revenue, earnings per share, operating
  income, and free cash flow (the series named in docs section 7).
  :func:`metrics.compound_annual_growth_rate` has no field here — it needs
  multi-year history beyond a single report pair.
- Composite scores nest the result classes defined in ``metrics.py``
  (per-signal and per-factor detail preserved); the Altman zone fields hold
  the ``metrics.Z_SAFE`` / ``Z_GREY`` / ``Z_DISTRESS`` strings.
"""

from dataclasses import dataclass

from metrics import BeneishResult, DuPontFiveFactor, DuPontThreeFactor, FScoreResult


@dataclass(frozen=True)
class CalculatedMetrics:
    """Every calculated result produced by the functions in ``metrics.py``,
    for a single company at a single point in time."""

    # ------------------------------------------------------------------
    # Building blocks shared across pillars
    # ------------------------------------------------------------------

    gross_profit: float | None = None
    earnings_before_interest_taxes_depreciation_and_amortization: float | None = None
    effective_tax_rate: float | None = None
    net_operating_profit_after_tax: float | None = None
    total_debt: float | None = None
    net_debt: float | None = None
    working_capital: float | None = None
    invested_capital: float | None = None
    earnings_per_share: float | None = None
    enterprise_value: float | None = None
    free_cash_flow: float | None = None

    # ------------------------------------------------------------------
    # Profitability
    # ------------------------------------------------------------------

    gross_profit_margin: float | None = None
    operating_margin: float | None = None
    net_profit_margin: float | None = None
    earnings_before_interest_taxes_depreciation_and_amortization_margin: float | None = None
    return_on_equity: float | None = None
    return_on_assets: float | None = None
    return_on_invested_capital: float | None = None

    # ------------------------------------------------------------------
    # Efficiency
    # ------------------------------------------------------------------

    total_asset_turnover: float | None = None
    fixed_asset_turnover: float | None = None
    working_capital_turnover: float | None = None
    days_inventory_on_hand: float | None = None
    days_sales_outstanding: float | None = None
    purchases: float | None = None
    days_payables_outstanding: float | None = None
    cash_conversion_cycle: float | None = None

    # ------------------------------------------------------------------
    # Liquidity
    # ------------------------------------------------------------------

    current_ratio: float | None = None
    quick_ratio: float | None = None
    cash_ratio: float | None = None
    operating_cash_flow_ratio: float | None = None
    defensive_interval_ratio: float | None = None

    # ------------------------------------------------------------------
    # Solvency & leverage
    # ------------------------------------------------------------------

    debt_to_equity: float | None = None
    debt_to_assets: float | None = None
    debt_to_capital: float | None = None
    financial_leverage: float | None = None
    net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization: float | None = None
    interest_coverage: float | None = None
    earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage: float | None = None
    operating_cash_flow_to_debt: float | None = None

    # ------------------------------------------------------------------
    # Cash flow - generation & quality
    # ------------------------------------------------------------------

    free_cash_flow_margin: float | None = None
    operating_cash_flow_to_net_income: float | None = None
    sloan_accruals_ratio: float | None = None
    free_cash_flow_conversion: float | None = None
    capital_expenditure_intensity: float | None = None
    capital_expenditures_to_depreciation: float | None = None

    # ------------------------------------------------------------------
    # Growth
    # ------------------------------------------------------------------

    revenue_growth: float | None = None
    earnings_per_share_growth: float | None = None
    operating_income_growth: float | None = None
    free_cash_flow_growth: float | None = None
    retention_rate: float | None = None
    sustainable_growth_rate: float | None = None
    reinvestment_rate: float | None = None
    fundamental_growth: float | None = None

    # ------------------------------------------------------------------
    # Valuation
    # ------------------------------------------------------------------

    price_to_earnings: float | None = None
    earnings_yield: float | None = None
    earnings_before_interest_and_taxes_to_enterprise_value: float | None = None
    price_to_book: float | None = None
    price_to_sales: float | None = None
    enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization: float | None = None
    enterprise_value_to_earnings_before_interest_and_taxes: float | None = None
    enterprise_value_to_sales: float | None = None
    free_cash_flow_yield: float | None = None
    dividend_yield: float | None = None
    payout_ratio: float | None = None
    shareholder_yield: float | None = None

    # ------------------------------------------------------------------
    # Composite scores
    # ------------------------------------------------------------------

    piotroski_f_score: FScoreResult | None = None
    altman_z_score: float | None = None
    altman_z_zone: str | None = None
    altman_z_double_prime: float | None = None
    altman_z_double_prime_zone: str | None = None
    dupont_three_factor: DuPontThreeFactor | None = None
    dupont_five_factor: DuPontFiveFactor | None = None
    beneish_m_score: BeneishResult | None = None
