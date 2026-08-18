"""Wire one period's parsed filing values through every calculation in
:mod:`calculations` and collect the results into a
:class:`calculated_metrics.CalculatedMetrics`.

Inputs are a :class:`stock_directory.StockInfo` (contributes market
capitalization, the one input not parseable from a filing) and a
:class:`quarterly_report_parse_result.QuarterlyReportParseResult` (one
reporting period).

Two conventions:

- The usually-absent components — lease obligations, preferred equity,
  minority interest, preferred dividends, and short-term investments — are
  treated as 0.0 when the parse result has ``None`` for them, matching the
  defaults in ``calculations.py``: most filers genuinely have none, and passing
  ``None`` through would wipe out total debt, enterprise value, and the
  liquidity ratios for the majority of companies. Dividends, buybacks, and
  stock issuance are NOT given this treatment (an absent tag is not provably
  a zero flow), so metrics built on them stay ``None`` when unreported.
- Metrics that need average balances, prior-period values, or
  period-over-period changes cannot be computed from a single parse result;
  they are descoped until multiple reports are supported and have no
  ``CalculatedMetrics`` fields — see ``docs/descoped_multi_period_metrics.md``.

Flow values arrive fiscal-year-to-date (the parse result's contract) and are
annualized to a run rate here — every flow field is multiplied by
4 / quarter number before any metric is computed. The uniform factor leaves
flow/flow metrics (margins, coverage, payout, cash-flow-to-net-income)
unchanged, while flow-vs-stock and flow-vs-market-cap metrics (valuation
ratios, yields, Altman terms) become run-rate annual, comparable to the
annual reference bands in ``calculated_metrics.py``.
"""

from stock_analyst import calculations
from stock_analyst.calculated_values import CalculatedValues
from stock_analyst.quantitative_data import RawQuantitativeData
from stock_analyst.stock_directory import StockInfo


def _zero_if_missing(value: float | None) -> float:
    return 0.0 if value is None else value


def run_all_calculations(
    stock_info: StockInfo, parse_result: RawQuantitativeData, fiscal_quarter: str
) -> CalculatedValues:
    """Compute every currently computable metric for one reporting period."""

    parse_result = parse_result.annualize_year_to_date_flow_values(fiscal_quarter)

    # Building blocks, computed first because later calculations consume them.
    gross_profit = calculations.gross_profit(parse_result.revenue, parse_result.cost_of_goods_sold)
    earnings_before_interest_taxes_depreciation_and_amortization = (
        calculations.earnings_before_interest_taxes_depreciation_and_amortization(
            parse_result.operating_income, parse_result.depreciation_and_amortization
        )
    )
    effective_tax_rate = calculations.effective_tax_rate(
        parse_result.income_tax_expense, parse_result.pretax_income
    )
    net_operating_profit_after_tax = calculations.net_operating_profit_after_tax(
        parse_result.operating_income, effective_tax_rate
    )
    total_debt = calculations.total_debt(
        parse_result.short_term_debt,
        parse_result.long_term_debt,
        _zero_if_missing(parse_result.lease_obligations),
    )
    net_debt = calculations.net_debt(
        total_debt,
        parse_result.cash_and_equivalents,
        _zero_if_missing(parse_result.short_term_investments),
    )
    working_capital = calculations.working_capital(
        parse_result.current_assets, parse_result.current_liabilities
    )
    invested_capital = calculations.invested_capital(
        total_debt, parse_result.shareholders_equity, parse_result.cash_and_equivalents
    )
    earnings_per_share = calculations.earnings_per_share(
        parse_result.net_income,
        parse_result.weighted_average_diluted_shares,
        _zero_if_missing(parse_result.preferred_dividends),
    )
    enterprise_value = calculations.enterprise_value(
        stock_info.market_cap,
        total_debt,
        parse_result.cash_and_equivalents,
        _zero_if_missing(parse_result.preferred_equity),
        _zero_if_missing(parse_result.minority_interest),
    )
    free_cash_flow = calculations.free_cash_flow(
        parse_result.operating_cash_flow, parse_result.capital_expenditures
    )
    common_equity = (
        None
        if parse_result.shareholders_equity is None
        else parse_result.shareholders_equity - _zero_if_missing(parse_result.preferred_equity)
    )
    payout_ratio = calculations.payout_ratio(parse_result.dividends_paid, parse_result.net_income)

    altman_z_score = calculations.altman_z_score(
        working_capital=working_capital,
        retained_earnings=parse_result.retained_earnings,
        earnings_before_interest_and_taxes=parse_result.operating_income,
        market_capitalization=stock_info.market_cap,
        total_liabilities=parse_result.total_liabilities,
        revenue=parse_result.revenue,
        total_assets=parse_result.total_assets,
    )
    altman_z_double_prime = calculations.altman_z_double_prime(
        working_capital=working_capital,
        retained_earnings=parse_result.retained_earnings,
        earnings_before_interest_and_taxes=parse_result.operating_income,
        book_equity=common_equity,
        total_liabilities=parse_result.total_liabilities,
        total_assets=parse_result.total_assets,
    )

    return CalculatedValues(
        # ------------------------------------------------------------------
        # Building blocks shared across pillars
        # ------------------------------------------------------------------
        gross_profit=gross_profit,
        earnings_before_interest_taxes_depreciation_and_amortization=(
            earnings_before_interest_taxes_depreciation_and_amortization
        ),
        effective_tax_rate=effective_tax_rate,
        net_operating_profit_after_tax=net_operating_profit_after_tax,
        total_debt=total_debt,
        net_debt=net_debt,
        working_capital=working_capital,
        invested_capital=invested_capital,
        earnings_per_share=earnings_per_share,
        enterprise_value=enterprise_value,
        free_cash_flow=free_cash_flow,
        # ------------------------------------------------------------------
        # Profitability
        # ------------------------------------------------------------------
        gross_profit_margin=calculations.gross_profit_margin(gross_profit, parse_result.revenue),
        operating_margin=calculations.operating_margin(
            parse_result.operating_income, parse_result.revenue
        ),
        net_profit_margin=calculations.net_profit_margin(parse_result.net_income, parse_result.revenue),
        earnings_before_interest_taxes_depreciation_and_amortization_margin=(
            calculations.earnings_before_interest_taxes_depreciation_and_amortization_margin(
                earnings_before_interest_taxes_depreciation_and_amortization,
                parse_result.revenue,
            )
        ),
        # ------------------------------------------------------------------
        # Liquidity
        # ------------------------------------------------------------------
        current_ratio=calculations.current_ratio(
            parse_result.current_assets, parse_result.current_liabilities
        ),
        quick_ratio=calculations.quick_ratio(
            parse_result.cash_and_equivalents,
            _zero_if_missing(parse_result.short_term_investments),
            parse_result.receivables,
            parse_result.current_liabilities,
        ),
        cash_ratio=calculations.cash_ratio(
            parse_result.cash_and_equivalents,
            _zero_if_missing(parse_result.short_term_investments),
            parse_result.current_liabilities,
        ),
        operating_cash_flow_ratio=calculations.operating_cash_flow_ratio(
            parse_result.operating_cash_flow, parse_result.current_liabilities
        ),
        defensive_interval_ratio=calculations.defensive_interval_ratio(
            parse_result.cash_and_equivalents,
            _zero_if_missing(parse_result.short_term_investments),
            parse_result.receivables,
            parse_result.operating_expenses,
            parse_result.non_cash_charges,
        ),
        # ------------------------------------------------------------------
        # Solvency & leverage
        # ------------------------------------------------------------------
        debt_to_equity=calculations.debt_to_equity(total_debt, parse_result.shareholders_equity),
        debt_to_assets=calculations.debt_to_assets(total_debt, parse_result.total_assets),
        debt_to_capital=calculations.debt_to_capital(total_debt, parse_result.shareholders_equity),
        net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization=(
            calculations.net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization(
                net_debt, earnings_before_interest_taxes_depreciation_and_amortization
            )
        ),
        interest_coverage=calculations.interest_coverage(
            parse_result.operating_income, parse_result.interest_expense
        ),
        earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage=(
            calculations.earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage(
                earnings_before_interest_taxes_depreciation_and_amortization,
                parse_result.interest_expense,
            )
        ),
        operating_cash_flow_to_debt=calculations.operating_cash_flow_to_debt(
            parse_result.operating_cash_flow, total_debt
        ),
        # ------------------------------------------------------------------
        # Cash flow - generation & quality
        # ------------------------------------------------------------------
        free_cash_flow_margin=calculations.free_cash_flow_margin(free_cash_flow, parse_result.revenue),
        operating_cash_flow_to_net_income=calculations.operating_cash_flow_to_net_income(
            parse_result.operating_cash_flow, parse_result.net_income
        ),
        sloan_accruals_ratio=calculations.sloan_accruals_ratio(
            parse_result.net_income,
            parse_result.operating_cash_flow,
            parse_result.investing_cash_flow,
            parse_result.total_assets,
        ),
        free_cash_flow_conversion=calculations.free_cash_flow_conversion(
            free_cash_flow, earnings_before_interest_taxes_depreciation_and_amortization
        ),
        capital_expenditure_intensity=calculations.capital_expenditure_intensity(
            parse_result.capital_expenditures, parse_result.revenue
        ),
        capital_expenditures_to_depreciation=calculations.capital_expenditures_to_depreciation(
            parse_result.capital_expenditures, parse_result.depreciation_and_amortization
        ),
        # ------------------------------------------------------------------
        # Growth
        # ------------------------------------------------------------------
        retention_rate=calculations.retention_rate(payout_ratio),
        # ------------------------------------------------------------------
        # Valuation
        # ------------------------------------------------------------------
        price_to_earnings=calculations.price_to_earnings(stock_info.market_cap, parse_result.net_income),
        earnings_yield=calculations.earnings_yield(parse_result.net_income, stock_info.market_cap),
        earnings_before_interest_and_taxes_to_enterprise_value=(
            calculations.earnings_before_interest_and_taxes_to_enterprise_value(
                parse_result.operating_income, enterprise_value
            )
        ),
        price_to_book=calculations.price_to_book(stock_info.market_cap, common_equity),
        price_to_sales=calculations.price_to_sales(stock_info.market_cap, parse_result.revenue),
        enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization=(
            calculations.enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization(
                enterprise_value, earnings_before_interest_taxes_depreciation_and_amortization
            )
        ),
        enterprise_value_to_earnings_before_interest_and_taxes=(
            calculations.enterprise_value_to_earnings_before_interest_and_taxes(
                enterprise_value, parse_result.operating_income
            )
        ),
        enterprise_value_to_sales=calculations.enterprise_value_to_sales(
            enterprise_value, parse_result.revenue
        ),
        free_cash_flow_yield=calculations.free_cash_flow_yield(free_cash_flow, stock_info.market_cap),
        dividend_yield=calculations.dividend_yield(parse_result.dividends_paid, stock_info.market_cap),
        payout_ratio=payout_ratio,
        shareholder_yield=calculations.shareholder_yield(
            parse_result.dividends_paid,
            parse_result.buybacks,
            parse_result.common_stock_issued,
            stock_info.market_cap,
        ),
        # ------------------------------------------------------------------
        # Composite scores
        # ------------------------------------------------------------------
        altman_z_score=altman_z_score,
        altman_z_zone=calculations.altman_z_zone(altman_z_score),
        altman_z_double_prime=altman_z_double_prime,
        altman_z_double_prime_zone=calculations.altman_z_double_prime_zone(altman_z_double_prime),
    )
