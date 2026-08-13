"""Pure calculation functions for the fundamental-analysis metrics defined in
docs/fundamental_metrics.md.

Conventions
-----------
- Inputs are plain numbers taken from financial statements (absolute amounts in
  the filing's currency, not per-share), plus market capitalization where
  noted. Nothing here fetches data; callers wire in values from whatever
  source they build.
- Flow inputs (revenue, net income, operating cash flow, capital
  expenditures, ...) must cover the same period, typically trailing twelve
  months. Balance-sheet inputs are point-in-time; where the convention calls
  for an average balance the parameter is named ``average_...`` (use
  :func:`average`).
- Capital expenditures, dividends paid, buybacks, and stock issuance are
  positive magnitudes (cash-flow-statement outflows/inflows with the sign
  stripped).
- Ratios are returned as decimal fractions (0.25 == 25%); day-count metrics
  return days.
- Every function returns ``None`` when an input is ``None``, a denominator is
  zero, or the metric is not meaningful for the given inputs (per the
  reference doc, e.g. price-to-earnings with non-positive earnings,
  debt-to-equity with non-positive equity). This mirrors the gaps that real
  XBRL data will have.
- Identifiers avoid abbreviations; the common short forms are noted in
  docstrings so they can be matched to the reference doc (for example,
  "earnings before interest, taxes, depreciation, and amortization" is
  commonly abbreviated EBITDA).
"""

from dataclasses import dataclass

DAYS_PER_YEAR = 365


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _present(*values: float | None) -> bool:
    return all(value is not None for value in values)


def _safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    if not _present(numerator, denominator) or denominator == 0:
        return None
    return numerator / denominator


def average(beginning: float | None, ending: float | None) -> float | None:
    """Average of beginning and ending balance-sheet values (CFA convention)."""
    if not _present(beginning, ending):
        return None
    return (beginning + ending) / 2


# ---------------------------------------------------------------------------
# Building blocks shared across pillars
# ---------------------------------------------------------------------------


def gross_profit(revenue: float | None, cost_of_goods_sold: float | None) -> float | None:
    if not _present(revenue, cost_of_goods_sold):
        return None
    return revenue - cost_of_goods_sold


def earnings_before_interest_taxes_depreciation_and_amortization(
    operating_income: float | None,
    depreciation_and_amortization: float | None,
) -> float | None:
    """Commonly abbreviated EBITDA: operating income plus depreciation and
    amortization (take the latter from the cash flow statement)."""
    if not _present(operating_income, depreciation_and_amortization):
        return None
    return operating_income + depreciation_and_amortization


def effective_tax_rate(income_tax_expense: float | None, pretax_income: float | None) -> float | None:
    """Income tax expense / pretax income; None when pretax income <= 0."""
    if not _present(income_tax_expense, pretax_income) or pretax_income <= 0:
        return None
    return income_tax_expense / pretax_income


def net_operating_profit_after_tax(
    earnings_before_interest_and_taxes: float | None,
    tax_rate: float | None,
) -> float | None:
    """Commonly abbreviated NOPAT: operating income x (1 - effective tax rate)."""
    if not _present(earnings_before_interest_and_taxes, tax_rate):
        return None
    return earnings_before_interest_and_taxes * (1 - tax_rate)


def total_debt(
    short_term_debt: float | None,
    long_term_debt: float | None,
    lease_obligations: float | None = 0.0,
) -> float | None:
    """All interest-bearing liabilities plus leases (Damodaran's definition)."""
    if not _present(short_term_debt, long_term_debt, lease_obligations):
        return None
    return short_term_debt + long_term_debt + lease_obligations


def net_debt(
    total_debt: float | None,
    cash_and_equivalents: float | None,
    marketable_securities: float | None = 0.0,
) -> float | None:
    """Total debt minus cash and marketable securities. Negative == net cash."""
    if not _present(total_debt, cash_and_equivalents, marketable_securities):
        return None
    return total_debt - cash_and_equivalents - marketable_securities


def working_capital(current_assets: float | None, current_liabilities: float | None) -> float | None:
    if not _present(current_assets, current_liabilities):
        return None
    return current_assets - current_liabilities


def invested_capital(
    total_debt: float | None,
    shareholders_equity: float | None,
    cash_and_equivalents: float | None,
) -> float | None:
    """Interest-bearing debt + equity - cash (cash netted out because interest
    income is not part of operating income)."""
    if not _present(total_debt, shareholders_equity, cash_and_equivalents):
        return None
    return total_debt + shareholders_equity - cash_and_equivalents


def earnings_per_share(
    net_income: float | None,
    weighted_average_shares: float | None,
    preferred_dividends: float | None = 0.0,
) -> float | None:
    if not _present(net_income, preferred_dividends):
        return None
    return _safe_divide(net_income - preferred_dividends, weighted_average_shares)


def enterprise_value(
    market_capitalization: float | None,
    total_debt: float | None,
    cash_and_equivalents: float | None,
    preferred_equity: float | None = 0.0,
    minority_interest: float | None = 0.0,
) -> float | None:
    """Market capitalization + total debt + preferred + minority interest - cash."""
    if not _present(
        market_capitalization, total_debt, cash_and_equivalents, preferred_equity, minority_interest
    ):
        return None
    return (
        market_capitalization
        + total_debt
        + preferred_equity
        + minority_interest
        - cash_and_equivalents
    )


def free_cash_flow(operating_cash_flow: float | None, capital_expenditures: float | None) -> float | None:
    """Cash flow from operations minus capital expenditures."""
    if not _present(operating_cash_flow, capital_expenditures):
        return None
    return operating_cash_flow - capital_expenditures


# ---------------------------------------------------------------------------
# Profitability
# ---------------------------------------------------------------------------


def gross_profit_margin(gross_profit: float | None, revenue: float | None) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_divide(gross_profit, revenue)


def operating_margin(operating_income: float | None, revenue: float | None) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_divide(operating_income, revenue)


def net_profit_margin(net_income: float | None, revenue: float | None) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_divide(net_income, revenue)


def earnings_before_interest_taxes_depreciation_and_amortization_margin(
    earnings_before_interest_taxes_depreciation_and_amortization: float | None,
    revenue: float | None,
) -> float | None:
    """Commonly abbreviated EBITDA margin."""
    if revenue is not None and revenue <= 0:
        return None
    return _safe_divide(earnings_before_interest_taxes_depreciation_and_amortization, revenue)


def return_on_equity(net_income: float | None, average_shareholders_equity: float | None) -> float | None:
    """None when average equity <= 0 (return on equity is meaningless with
    negative book equity - fall back to return on invested capital)."""
    if average_shareholders_equity is not None and average_shareholders_equity <= 0:
        return None
    return _safe_divide(net_income, average_shareholders_equity)


def return_on_assets(net_income: float | None, average_total_assets: float | None) -> float | None:
    if average_total_assets is not None and average_total_assets <= 0:
        return None
    return _safe_divide(net_income, average_total_assets)


def return_on_invested_capital(
    net_operating_profit_after_tax: float | None,
    average_invested_capital: float | None,
) -> float | None:
    """None when average invested capital <= 0."""
    if average_invested_capital is not None and average_invested_capital <= 0:
        return None
    return _safe_divide(net_operating_profit_after_tax, average_invested_capital)


def return_on_net_operating_assets(
    after_tax_operating_income: float | None,
    net_operating_assets: float | None,
) -> float | None:
    """RNOA (Penman). Caller must supply reformulated inputs: net operating
    assets = operating assets - operating liabilities, financing items
    excluded from both sides."""
    if net_operating_assets is not None and net_operating_assets <= 0:
        return None
    return _safe_divide(after_tax_operating_income, net_operating_assets)


# ---------------------------------------------------------------------------
# Efficiency
# ---------------------------------------------------------------------------


def total_asset_turnover(revenue: float | None, average_total_assets: float | None) -> float | None:
    if average_total_assets is not None and average_total_assets <= 0:
        return None
    return _safe_divide(revenue, average_total_assets)


def fixed_asset_turnover(revenue: float | None, average_net_fixed_assets: float | None) -> float | None:
    if average_net_fixed_assets is not None and average_net_fixed_assets <= 0:
        return None
    return _safe_divide(revenue, average_net_fixed_assets)


def working_capital_turnover(revenue: float | None, average_working_capital: float | None) -> float | None:
    """None when average working capital <= 0 (CFA: uninterpretable there)."""
    if average_working_capital is not None and average_working_capital <= 0:
        return None
    return _safe_divide(revenue, average_working_capital)


def days_inventory_on_hand(
    cost_of_goods_sold: float | None,
    average_inventory: float | None,
) -> float | None:
    if not _present(cost_of_goods_sold, average_inventory):
        return None
    if cost_of_goods_sold <= 0 or average_inventory <= 0:
        return None
    return DAYS_PER_YEAR / (cost_of_goods_sold / average_inventory)


def days_sales_outstanding(revenue: float | None, average_receivables: float | None) -> float | None:
    if not _present(revenue, average_receivables) or revenue <= 0 or average_receivables <= 0:
        return None
    return DAYS_PER_YEAR / (revenue / average_receivables)


def purchases(cost_of_goods_sold: float | None, inventory_change: float | None) -> float | None:
    """Purchases ~= cost of goods sold + change in inventory (ending - beginning)."""
    if not _present(cost_of_goods_sold, inventory_change):
        return None
    return cost_of_goods_sold + inventory_change


def days_payables_outstanding(purchases: float | None, average_payables: float | None) -> float | None:
    """Pass cost of goods sold as the accepted fallback when purchases can't
    be derived."""
    if not _present(purchases, average_payables) or purchases <= 0 or average_payables <= 0:
        return None
    return DAYS_PER_YEAR / (purchases / average_payables)


def cash_conversion_cycle(
    days_inventory: float | None,
    days_sales: float | None,
    days_payables: float | None,
) -> float | None:
    """Days inventory + days sales - days payables. Negative means suppliers
    finance the operation."""
    if not _present(days_inventory, days_sales, days_payables):
        return None
    return days_inventory + days_sales - days_payables


# ---------------------------------------------------------------------------
# Liquidity
# ---------------------------------------------------------------------------


def current_ratio(current_assets: float | None, current_liabilities: float | None) -> float | None:
    if current_liabilities is not None and current_liabilities <= 0:
        return None
    return _safe_divide(current_assets, current_liabilities)


def quick_ratio(
    cash_and_equivalents: float | None,
    short_term_investments: float | None,
    receivables: float | None,
    current_liabilities: float | None,
) -> float | None:
    if not _present(cash_and_equivalents, short_term_investments, receivables):
        return None
    if current_liabilities is not None and current_liabilities <= 0:
        return None
    return _safe_divide(
        cash_and_equivalents + short_term_investments + receivables, current_liabilities
    )


def cash_ratio(
    cash_and_equivalents: float | None,
    short_term_investments: float | None,
    current_liabilities: float | None,
) -> float | None:
    if not _present(cash_and_equivalents, short_term_investments):
        return None
    if current_liabilities is not None and current_liabilities <= 0:
        return None
    return _safe_divide(cash_and_equivalents + short_term_investments, current_liabilities)


def operating_cash_flow_ratio(
    operating_cash_flow: float | None,
    current_liabilities: float | None,
) -> float | None:
    if current_liabilities is not None and current_liabilities <= 0:
        return None
    return _safe_divide(operating_cash_flow, current_liabilities)


def defensive_interval_ratio(
    cash_and_equivalents: float | None,
    short_term_investments: float | None,
    receivables: float | None,
    operating_expenses: float | None,
    non_cash_charges: float | None,
) -> float | None:
    """Days the firm can operate on liquid assets with zero revenue."""
    if not _present(cash_and_equivalents, short_term_investments, receivables,
                    operating_expenses, non_cash_charges):
        return None
    daily_expenditures = (operating_expenses - non_cash_charges) / DAYS_PER_YEAR
    if daily_expenditures <= 0:
        return None
    return (cash_and_equivalents + short_term_investments + receivables) / daily_expenditures


# ---------------------------------------------------------------------------
# Solvency & leverage
# ---------------------------------------------------------------------------


def debt_to_equity(total_debt: float | None, shareholders_equity: float | None) -> float | None:
    """None when equity <= 0 (fall back to debt_to_capital / debt_to_assets)."""
    if shareholders_equity is not None and shareholders_equity <= 0:
        return None
    return _safe_divide(total_debt, shareholders_equity)


def debt_to_assets(total_debt: float | None, total_assets: float | None) -> float | None:
    if total_assets is not None and total_assets <= 0:
        return None
    return _safe_divide(total_debt, total_assets)


def debt_to_capital(total_debt: float | None, shareholders_equity: float | None) -> float | None:
    if not _present(total_debt, shareholders_equity):
        return None
    capital = total_debt + shareholders_equity
    if capital <= 0:
        return None
    return total_debt / capital


def financial_leverage(
    average_total_assets: float | None,
    average_total_equity: float | None,
) -> float | None:
    """Equity multiplier (assets / equity); the leverage leg of DuPont and the
    leverage measure that stays meaningful for banks."""
    if average_total_equity is not None and average_total_equity <= 0:
        return None
    return _safe_divide(average_total_assets, average_total_equity)


def net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization(
    net_debt: float | None,
    earnings_before_interest_taxes_depreciation_and_amortization: float | None,
) -> float | None:
    """Commonly abbreviated net debt / EBITDA. None when the earnings figure
    is <= 0. A negative result means net cash."""
    denominator = earnings_before_interest_taxes_depreciation_and_amortization
    if denominator is not None and denominator <= 0:
        return None
    return _safe_divide(net_debt, denominator)


def interest_coverage(
    earnings_before_interest_and_taxes: float | None,
    interest_expense: float | None,
) -> float | None:
    """Operating income / gross interest expense. None when interest expense
    <= 0 (no debt -> "not meaningful", per the reference doc)."""
    if interest_expense is not None and interest_expense <= 0:
        return None
    return _safe_divide(earnings_before_interest_and_taxes, interest_expense)


def earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage(
    earnings_before_interest_taxes_depreciation_and_amortization: float | None,
    interest_expense: float | None,
) -> float | None:
    """Commonly abbreviated EBITDA / interest."""
    if interest_expense is not None and interest_expense <= 0:
        return None
    return _safe_divide(
        earnings_before_interest_taxes_depreciation_and_amortization, interest_expense
    )


def fixed_charge_coverage(
    earnings_before_interest_and_taxes: float | None,
    lease_payments: float | None,
    interest_expense: float | None,
) -> float | None:
    if not _present(earnings_before_interest_and_taxes, lease_payments, interest_expense):
        return None
    charges = interest_expense + lease_payments
    if charges <= 0:
        return None
    return (earnings_before_interest_and_taxes + lease_payments) / charges


def operating_cash_flow_to_debt(
    operating_cash_flow: float | None,
    total_debt: float | None,
) -> float | None:
    if total_debt is not None and total_debt <= 0:
        return None
    return _safe_divide(operating_cash_flow, total_debt)


# ---------------------------------------------------------------------------
# Cash flow - generation & quality
# ---------------------------------------------------------------------------


def free_cash_flow_margin(free_cash_flow: float | None, revenue: float | None) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_divide(free_cash_flow, revenue)


def operating_cash_flow_to_net_income(
    operating_cash_flow: float | None,
    net_income: float | None,
) -> float | None:
    """Earnings-quality check; persistently >= 1 is healthy. None when net
    income <= 0 (the ratio explodes near zero - use sloan_accruals_ratio)."""
    if net_income is not None and net_income <= 0:
        return None
    return _safe_divide(operating_cash_flow, net_income)


def sloan_accruals_ratio(
    net_income: float | None,
    operating_cash_flow: float | None,
    investing_cash_flow: float | None,
    total_assets: float | None,
) -> float | None:
    """(Net income - operating cash flow - investing cash flow) / total
    assets. Between -0.10 and +0.10 is considered safe; above +0.25 is a
    strong warning (Sloan 1996). ``investing_cash_flow`` keeps its
    cash-flow-statement sign (usually negative)."""
    if not _present(net_income, operating_cash_flow, investing_cash_flow):
        return None
    if total_assets is None or total_assets <= 0:
        return None
    return (net_income - operating_cash_flow - investing_cash_flow) / total_assets


def free_cash_flow_conversion(
    free_cash_flow: float | None,
    earnings_before_interest_taxes_depreciation_and_amortization: float | None,
) -> float | None:
    """Free cash flow / EBITDA; >= 0.8 strong, ~1.0 ideal."""
    denominator = earnings_before_interest_taxes_depreciation_and_amortization
    if denominator is not None and denominator <= 0:
        return None
    return _safe_divide(free_cash_flow, denominator)


def capital_expenditure_intensity(
    capital_expenditures: float | None,
    revenue: float | None,
) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_divide(capital_expenditures, revenue)


def capital_expenditures_to_depreciation(
    capital_expenditures: float | None,
    depreciation_and_amortization: float | None,
) -> float | None:
    """>1 growing asset base; <1 possible underinvestment (rough maintenance-
    capital-expenditure proxy)."""
    if depreciation_and_amortization is not None and depreciation_and_amortization <= 0:
        return None
    return _safe_divide(capital_expenditures, depreciation_and_amortization)


# ---------------------------------------------------------------------------
# Growth
# ---------------------------------------------------------------------------


def growth_rate(current: float | None, prior: float | None) -> float | None:
    """Period-over-period growth. None when the base period is <= 0 (growth
    off a non-positive base is meaningless)."""
    if not _present(current, prior) or prior <= 0:
        return None
    return (current - prior) / prior


def compound_annual_growth_rate(
    latest: float | None,
    earliest: float | None,
    periods: float | None,
) -> float | None:
    """Commonly abbreviated CAGR, over ``periods`` years."""
    if not _present(latest, earliest, periods) or earliest <= 0 or latest <= 0 or periods <= 0:
        return None
    return (latest / earliest) ** (1 / periods) - 1


def retention_rate(payout_ratio: float | None) -> float | None:
    if payout_ratio is None:
        return None
    return 1 - payout_ratio


def sustainable_growth_rate(
    return_on_equity: float | None,
    payout_ratio: float | None,
) -> float | None:
    """Retention rate x return on equity - growth fundable from retained
    earnings."""
    retention = retention_rate(payout_ratio)
    if not _present(return_on_equity, retention):
        return None
    return return_on_equity * retention


def reinvestment_rate(
    capital_expenditures: float | None,
    depreciation_and_amortization: float | None,
    change_in_working_capital: float | None,
    net_operating_profit_after_tax: float | None,
) -> float | None:
    """(Net capital expenditures + change in non-cash working capital) /
    net operating profit after tax (Damodaran). None when the denominator
    <= 0. Average over several years - capital spending is lumpy."""
    if not _present(capital_expenditures, depreciation_and_amortization, change_in_working_capital):
        return None
    if net_operating_profit_after_tax is None or net_operating_profit_after_tax <= 0:
        return None
    return (
        capital_expenditures - depreciation_and_amortization + change_in_working_capital
    ) / net_operating_profit_after_tax


def fundamental_growth(
    reinvestment_rate: float | None,
    return_on_invested_capital: float | None,
) -> float | None:
    """Expected operating-income growth = reinvestment rate x return on
    invested capital."""
    if not _present(reinvestment_rate, return_on_invested_capital):
        return None
    return reinvestment_rate * return_on_invested_capital


# ---------------------------------------------------------------------------
# Valuation (market-capitalization form; see docs section 8 for the
# enterprise-value definition)
# ---------------------------------------------------------------------------


def price_to_earnings(
    market_capitalization: float | None,
    net_income: float | None,
) -> float | None:
    """Trailing price-to-earnings. None when earnings <= 0 (undefined; rank
    on earnings_yield instead)."""
    if net_income is not None and net_income <= 0:
        return None
    return _safe_divide(market_capitalization, net_income)


def earnings_yield(net_income: float | None, market_capitalization: float | None) -> float | None:
    """Earnings / price - defined even for negative earnings, so it ranks the
    full universe."""
    if market_capitalization is not None and market_capitalization <= 0:
        return None
    return _safe_divide(net_income, market_capitalization)


def earnings_before_interest_and_taxes_to_enterprise_value(
    earnings_before_interest_and_taxes: float | None,
    enterprise_value: float | None,
) -> float | None:
    """Greenblatt's earnings yield: capital-structure-neutral earnings/price."""
    if enterprise_value is not None and enterprise_value <= 0:
        return None
    return _safe_divide(earnings_before_interest_and_taxes, enterprise_value)


def price_to_book(
    market_capitalization: float | None,
    common_equity: float | None,
) -> float | None:
    """None when book equity <= 0."""
    if common_equity is not None and common_equity <= 0:
        return None
    return _safe_divide(market_capitalization, common_equity)


def price_to_sales(market_capitalization: float | None, revenue: float | None) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_divide(market_capitalization, revenue)


def enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization(
    enterprise_value: float | None,
    earnings_before_interest_taxes_depreciation_and_amortization: float | None,
) -> float | None:
    """Commonly abbreviated EV/EBITDA. None when the earnings figure is <= 0
    (fall back to enterprise_value_to_sales)."""
    denominator = earnings_before_interest_taxes_depreciation_and_amortization
    if denominator is not None and denominator <= 0:
        return None
    return _safe_divide(enterprise_value, denominator)


def enterprise_value_to_earnings_before_interest_and_taxes(
    enterprise_value: float | None,
    earnings_before_interest_and_taxes: float | None,
) -> float | None:
    """Commonly abbreviated EV/EBIT."""
    if earnings_before_interest_and_taxes is not None and earnings_before_interest_and_taxes <= 0:
        return None
    return _safe_divide(enterprise_value, earnings_before_interest_and_taxes)


def enterprise_value_to_sales(
    enterprise_value: float | None,
    revenue: float | None,
) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_divide(enterprise_value, revenue)


def free_cash_flow_yield(
    free_cash_flow: float | None,
    market_capitalization: float | None,
) -> float | None:
    """Free cash flow / market capitalization (equity form).
    Price-to-free-cash-flow is its inverse."""
    if market_capitalization is not None and market_capitalization <= 0:
        return None
    return _safe_divide(free_cash_flow, market_capitalization)


def dividend_yield(
    dividends_paid: float | None,
    market_capitalization: float | None,
) -> float | None:
    """Trailing-paid yield: common dividends paid (trailing twelve months) /
    market capitalization."""
    if market_capitalization is not None and market_capitalization <= 0:
        return None
    return _safe_divide(dividends_paid, market_capitalization)


def payout_ratio(dividends_paid: float | None, net_income: float | None) -> float | None:
    """Dividends / net income. None when net income <= 0 (payout off losses
    is unsustainable by definition - compare dividends to free cash flow
    instead)."""
    if net_income is not None and net_income <= 0:
        return None
    return _safe_divide(dividends_paid, net_income)


def shareholder_yield(
    dividends_paid: float | None,
    buybacks: float | None,
    stock_issued: float | None,
    market_capitalization: float | None,
) -> float | None:
    """(Dividends + buybacks - issuance) / market capitalization. Net of
    issuance so that buybacks merely offsetting stock-compensation dilution
    don't count."""
    if not _present(dividends_paid, buybacks, stock_issued):
        return None
    if market_capitalization is None or market_capitalization <= 0:
        return None
    return (dividends_paid + buybacks - stock_issued) / market_capitalization


# ---------------------------------------------------------------------------
# Composite: Piotroski F-Score
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FScoreResult:
    """F-Score with per-signal detail. ``signals`` maps signal name to True
    (point earned), False (no point), or None (not evaluable from the inputs).
    ``score`` counts True signals; ``max_score`` counts evaluable ones, so a
    partial-data score of 5/6 reads differently from 5/9."""

    score: int
    max_score: int
    signals: dict[str, bool | None]


def piotroski_f_score(
    *,
    net_income: float | None,
    net_income_prior: float | None,
    operating_cash_flow: float | None,
    beginning_total_assets: float | None,
    beginning_total_assets_prior: float | None,
    long_term_debt: float | None,
    long_term_debt_prior: float | None,
    average_total_assets: float | None,
    average_total_assets_prior: float | None,
    current_assets: float | None,
    current_liabilities: float | None,
    current_assets_prior: float | None,
    current_liabilities_prior: float | None,
    revenue: float | None,
    revenue_prior: float | None,
    cost_of_goods_sold: float | None,
    cost_of_goods_sold_prior: float | None,
    common_stock_issued: float | None,
) -> FScoreResult:
    """Piotroski (2000) nine-signal score; see docs section 9.

    ``beginning_total_assets`` is total assets at the *start* of the current
    year (== prior year-end); ``_prior`` variants are the same inputs one year
    earlier. ``common_stock_issued`` is the cash raised from common-stock
    issuance in the current year (0 or None-as-unknown; only an explicit 0
    earns the no-issuance point). Apply within cheap (high book-to-market)
    non-financial stocks, per the original paper.
    """

    def _scaled_by_beginning_assets(value: float | None, assets: float | None) -> float | None:
        if assets is None or assets <= 0:
            return None
        return _safe_divide(value, assets)

    return_on_assets_current = _scaled_by_beginning_assets(net_income, beginning_total_assets)
    return_on_assets_prior = _scaled_by_beginning_assets(
        net_income_prior, beginning_total_assets_prior
    )
    operating_cash_flow_scaled = _scaled_by_beginning_assets(
        operating_cash_flow, beginning_total_assets
    )

    leverage = _safe_divide(long_term_debt, average_total_assets)
    leverage_prior = _safe_divide(long_term_debt_prior, average_total_assets_prior)

    current_ratio_current = current_ratio(current_assets, current_liabilities)
    current_ratio_prior = current_ratio(current_assets_prior, current_liabilities_prior)

    gross_margin_current = gross_profit_margin(gross_profit(revenue, cost_of_goods_sold), revenue)
    gross_margin_prior = gross_profit_margin(
        gross_profit(revenue_prior, cost_of_goods_sold_prior), revenue_prior
    )

    asset_turnover_current = _scaled_by_beginning_assets(revenue, beginning_total_assets)
    asset_turnover_prior = _scaled_by_beginning_assets(
        revenue_prior, beginning_total_assets_prior
    )

    def _increased(current: float | None, prior: float | None) -> bool | None:
        return None if not _present(current, prior) else current > prior

    def _decreased(current: float | None, prior: float | None) -> bool | None:
        return None if not _present(current, prior) else current < prior

    signals: dict[str, bool | None] = {
        "positive_return_on_assets": (
            None if return_on_assets_current is None else return_on_assets_current > 0
        ),
        "positive_operating_cash_flow": (
            None if operating_cash_flow_scaled is None else operating_cash_flow_scaled > 0
        ),
        "improving_return_on_assets": _increased(return_on_assets_current, return_on_assets_prior),
        "operating_cash_flow_exceeds_net_income": _increased(operating_cash_flow, net_income),
        "decreasing_leverage": _decreased(leverage, leverage_prior),
        "improving_current_ratio": _increased(current_ratio_current, current_ratio_prior),
        "no_stock_issuance": None if common_stock_issued is None else common_stock_issued <= 0,
        "improving_gross_margin": _increased(gross_margin_current, gross_margin_prior),
        "improving_asset_turnover": _increased(asset_turnover_current, asset_turnover_prior),
    }
    return FScoreResult(
        score=sum(1 for value in signals.values() if value is True),
        max_score=sum(1 for value in signals.values() if value is not None),
        signals=signals,
    )


# ---------------------------------------------------------------------------
# Composite: Altman Z-Score
# ---------------------------------------------------------------------------

Z_SAFE, Z_GREY, Z_DISTRESS = "safe", "grey", "distress"


def altman_z_score(
    *,
    working_capital: float | None,
    retained_earnings: float | None,
    earnings_before_interest_and_taxes: float | None,
    market_capitalization: float | None,
    total_liabilities: float | None,
    revenue: float | None,
    total_assets: float | None,
) -> float | None:
    """Original Altman (1968) model for public manufacturers (SIC 2000-3999).
    Never apply to financials. Use altman_z_zone to interpret."""
    if not _present(
        working_capital,
        retained_earnings,
        earnings_before_interest_and_taxes,
        market_capitalization,
        revenue,
    ):
        return None
    if not _present(total_liabilities, total_assets) or total_assets <= 0 or total_liabilities <= 0:
        return None
    return (
        1.2 * (working_capital / total_assets)
        + 1.4 * (retained_earnings / total_assets)
        + 3.3 * (earnings_before_interest_and_taxes / total_assets)
        + 0.6 * (market_capitalization / total_liabilities)
        + 1.0 * (revenue / total_assets)
    )


def altman_z_zone(z_score: float | None) -> str | None:
    """Zones for the original model: safe > 2.99, distress < 1.81."""
    if z_score is None:
        return None
    if z_score > 2.99:
        return Z_SAFE
    if z_score < 1.81:
        return Z_DISTRESS
    return Z_GREY


def altman_z_double_prime(
    *,
    working_capital: float | None,
    retained_earnings: float | None,
    earnings_before_interest_and_taxes: float | None,
    book_equity: float | None,
    total_liabilities: float | None,
    total_assets: float | None,
) -> float | None:
    """Z'' variant for non-manufacturers (drops asset turnover, book equity in
    the fourth term). Never apply to financials. Use
    altman_z_double_prime_zone."""
    if not _present(
        working_capital, retained_earnings, earnings_before_interest_and_taxes, book_equity
    ):
        return None
    if not _present(total_liabilities, total_assets) or total_assets <= 0 or total_liabilities <= 0:
        return None
    return (
        6.56 * (working_capital / total_assets)
        + 3.26 * (retained_earnings / total_assets)
        + 6.72 * (earnings_before_interest_and_taxes / total_assets)
        + 1.05 * (book_equity / total_liabilities)
    )


def altman_z_double_prime_zone(z_score: float | None) -> str | None:
    """Zones for Z'': safe > 2.6, distress < 1.1."""
    if z_score is None:
        return None
    if z_score > 2.6:
        return Z_SAFE
    if z_score < 1.1:
        return Z_DISTRESS
    return Z_GREY


# ---------------------------------------------------------------------------
# Composite: DuPont decomposition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DuPontThreeFactor:
    net_margin: float
    asset_turnover: float
    equity_multiplier: float

    @property
    def return_on_equity(self) -> float:
        return self.net_margin * self.asset_turnover * self.equity_multiplier


@dataclass(frozen=True)
class DuPontFiveFactor:
    tax_burden: float
    interest_burden: float
    operating_income_margin: float
    asset_turnover: float
    equity_multiplier: float

    @property
    def return_on_equity(self) -> float:
        return (
            self.tax_burden
            * self.interest_burden
            * self.operating_income_margin
            * self.asset_turnover
            * self.equity_multiplier
        )


def dupont_three_factor(
    *,
    net_income: float | None,
    revenue: float | None,
    average_total_assets: float | None,
    average_total_equity: float | None,
) -> DuPontThreeFactor | None:
    """Return on equity = net margin x asset turnover x equity multiplier.
    High return on equity from margin/turnover is operationally earned; from
    the multiplier, leverage-manufactured."""
    margin = net_profit_margin(net_income, revenue)
    turnover = total_asset_turnover(revenue, average_total_assets)
    multiplier = financial_leverage(average_total_assets, average_total_equity)
    if not _present(margin, turnover, multiplier):
        return None
    return DuPontThreeFactor(
        net_margin=margin, asset_turnover=turnover, equity_multiplier=multiplier
    )


def dupont_five_factor(
    *,
    net_income: float | None,
    pretax_income: float | None,
    earnings_before_interest_and_taxes: float | None,
    revenue: float | None,
    average_total_assets: float | None,
    average_total_equity: float | None,
) -> DuPontFiveFactor | None:
    """Return on equity = tax burden x interest burden x operating income
    margin x asset turnover x equity multiplier. Uninterpretable (None) when
    pretax income or operating income <= 0."""
    if not _present(pretax_income, earnings_before_interest_and_taxes):
        return None
    if pretax_income <= 0 or earnings_before_interest_and_taxes <= 0:
        return None
    tax_burden = _safe_divide(net_income, pretax_income)
    interest_burden = pretax_income / earnings_before_interest_and_taxes
    margin = operating_margin(earnings_before_interest_and_taxes, revenue)
    turnover = total_asset_turnover(revenue, average_total_assets)
    multiplier = financial_leverage(average_total_assets, average_total_equity)
    if not _present(tax_burden, margin, turnover, multiplier):
        return None
    return DuPontFiveFactor(
        tax_burden=tax_burden,
        interest_burden=interest_burden,
        operating_income_margin=margin,
        asset_turnover=turnover,
        equity_multiplier=multiplier,
    )


# ---------------------------------------------------------------------------
# Composite: Beneish M-Score
# ---------------------------------------------------------------------------

M_SCORE_THRESHOLD = -1.78


@dataclass(frozen=True)
class BeneishPeriod:
    """One fiscal year of inputs for the M-Score. All from filings."""

    revenue: float
    cost_of_goods_sold: float
    receivables: float
    current_assets: float
    net_property_plant_and_equipment: float
    total_assets: float
    depreciation: float
    selling_general_and_administrative_expense: float
    long_term_debt: float
    current_liabilities: float
    income_from_continuing_operations: float
    operating_cash_flow: float


@dataclass(frozen=True)
class BeneishResult:
    m_score: float
    indices: dict[str, float]

    @property
    def likely_manipulator(self) -> bool:
        """M > -1.78 flags a likely earnings manipulator (Beneish 1999)."""
        return self.m_score > M_SCORE_THRESHOLD


def beneish_m_score(current: BeneishPeriod, prior: BeneishPeriod) -> BeneishResult | None:
    """Beneish (1999) eight-variable earnings-manipulation score; see docs
    section 9. A red flag, not a rating. Never score financials. Returns None
    when any index is uncomputable (zero denominators)."""

    def _ratio(numerator: float, denominator: float) -> float | None:
        return None if denominator == 0 else numerator / denominator

    def _receivable_days(period: BeneishPeriod) -> float | None:
        return _ratio(period.receivables, period.revenue)

    def _gross_margin(period: BeneishPeriod) -> float | None:
        if period.revenue == 0:
            return None
        return (period.revenue - period.cost_of_goods_sold) / period.revenue

    def _soft_assets(period: BeneishPeriod) -> float | None:
        if period.total_assets == 0:
            return None
        return 1 - (
            period.current_assets + period.net_property_plant_and_equipment
        ) / period.total_assets

    def _depreciation_rate(period: BeneishPeriod) -> float | None:
        return _ratio(
            period.depreciation,
            period.depreciation + period.net_property_plant_and_equipment,
        )

    def _selling_general_and_administrative_ratio(period: BeneishPeriod) -> float | None:
        return _ratio(period.selling_general_and_administrative_expense, period.revenue)

    def _leverage(period: BeneishPeriod) -> float | None:
        return _ratio(period.long_term_debt + period.current_liabilities, period.total_assets)

    pairs = {
        "days_sales_in_receivables_index": (_receivable_days(current), _receivable_days(prior)),
        "gross_margin_index": (_gross_margin(prior), _gross_margin(current)),  # prior over current
        "asset_quality_index": (_soft_assets(current), _soft_assets(prior)),
        "sales_growth_index": (current.revenue, prior.revenue),
        "depreciation_index": (
            _depreciation_rate(prior),
            _depreciation_rate(current),
        ),  # prior over current
        "selling_general_and_administrative_index": (
            _selling_general_and_administrative_ratio(current),
            _selling_general_and_administrative_ratio(prior),
        ),
        "leverage_index": (_leverage(current), _leverage(prior)),
    }
    indices: dict[str, float] = {}
    for name, (numerator, denominator) in pairs.items():
        index = None if not _present(numerator, denominator) else _ratio(numerator, denominator)
        if index is None:
            return None
        indices[name] = index

    if current.total_assets == 0:
        return None
    indices["total_accruals_to_total_assets"] = (
        current.income_from_continuing_operations - current.operating_cash_flow
    ) / current.total_assets

    m_score = (
        -4.840
        + 0.920 * indices["days_sales_in_receivables_index"]
        + 0.528 * indices["gross_margin_index"]
        + 0.404 * indices["asset_quality_index"]
        + 0.892 * indices["sales_growth_index"]
        + 0.115 * indices["depreciation_index"]
        - 0.172 * indices["selling_general_and_administrative_index"]
        - 0.327 * indices["leverage_index"]
        + 4.679 * indices["total_accruals_to_total_assets"]
    )
    return BeneishResult(m_score=m_score, indices=indices)
