"""Pure calculation functions for the fundamental-analysis metrics defined in
docs/fundamental_metrics.md.

Conventions
-----------
- Inputs are plain numbers taken from financial statements (absolute amounts in
  the filing's currency, not per-share), plus market cap where noted. Nothing
  here fetches data; callers wire in values from whatever source they build.
- Flow inputs (revenue, net income, CFO, capex, ...) must cover the same
  period, typically trailing twelve months. Balance-sheet inputs are
  point-in-time; where the convention calls for an average balance the
  parameter is named ``avg_...`` (use :func:`average`).
- Capex, dividends paid, buybacks, and stock issuance are positive magnitudes
  (cash-flow-statement outflows/inflows with the sign stripped).
- Ratios are returned as decimal fractions (0.25 == 25%); day-count metrics
  return days.
- Every function returns ``None`` when an input is ``None``, a denominator is
  zero, or the metric is not meaningful for the given inputs (per the
  reference doc, e.g. P/E with non-positive earnings, debt-to-equity with
  non-positive equity). This mirrors the gaps that real XBRL data will have.
"""

from dataclasses import dataclass

DAYS_PER_YEAR = 365


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _present(*values: float | None) -> bool:
    return all(v is not None for v in values)


def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
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


def gross_profit(revenue: float | None, cogs: float | None) -> float | None:
    if not _present(revenue, cogs):
        return None
    return revenue - cogs


def ebitda(operating_income: float | None, depreciation_amortization: float | None) -> float | None:
    """EBITDA = operating income + D&A (take D&A from the cash flow statement)."""
    if not _present(operating_income, depreciation_amortization):
        return None
    return operating_income + depreciation_amortization


def effective_tax_rate(income_tax_expense: float | None, pretax_income: float | None) -> float | None:
    """Income tax expense / pretax income; None when pretax income <= 0."""
    if not _present(income_tax_expense, pretax_income) or pretax_income <= 0:
        return None
    return income_tax_expense / pretax_income


def nopat(ebit: float | None, tax_rate: float | None) -> float | None:
    """Net operating profit after tax = EBIT x (1 - effective tax rate)."""
    if not _present(ebit, tax_rate):
        return None
    return ebit * (1 - tax_rate)


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
    return _safe_div(net_income - preferred_dividends, weighted_average_shares)


def enterprise_value(
    market_cap: float | None,
    total_debt: float | None,
    cash_and_equivalents: float | None,
    preferred_equity: float | None = 0.0,
    minority_interest: float | None = 0.0,
) -> float | None:
    """EV = market cap + total debt + preferred + minority interest - cash."""
    if not _present(market_cap, total_debt, cash_and_equivalents, preferred_equity, minority_interest):
        return None
    return market_cap + total_debt + preferred_equity + minority_interest - cash_and_equivalents


def free_cash_flow(cfo: float | None, capex: float | None) -> float | None:
    """FCF = cash flow from operations - capital expenditures."""
    if not _present(cfo, capex):
        return None
    return cfo - capex


# ---------------------------------------------------------------------------
# Profitability
# ---------------------------------------------------------------------------


def gross_profit_margin(gross_profit: float | None, revenue: float | None) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_div(gross_profit, revenue)


def operating_margin(operating_income: float | None, revenue: float | None) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_div(operating_income, revenue)


def net_profit_margin(net_income: float | None, revenue: float | None) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_div(net_income, revenue)


def ebitda_margin(ebitda: float | None, revenue: float | None) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_div(ebitda, revenue)


def return_on_equity(net_income: float | None, avg_shareholders_equity: float | None) -> float | None:
    """None when average equity <= 0 (ROE is meaningless with negative book
    equity - fall back to ROIC)."""
    if avg_shareholders_equity is not None and avg_shareholders_equity <= 0:
        return None
    return _safe_div(net_income, avg_shareholders_equity)


def return_on_assets(net_income: float | None, avg_total_assets: float | None) -> float | None:
    if avg_total_assets is not None and avg_total_assets <= 0:
        return None
    return _safe_div(net_income, avg_total_assets)


def return_on_invested_capital(nopat: float | None, avg_invested_capital: float | None) -> float | None:
    """None when average invested capital <= 0."""
    if avg_invested_capital is not None and avg_invested_capital <= 0:
        return None
    return _safe_div(nopat, avg_invested_capital)


def return_on_net_operating_assets(
    after_tax_operating_income: float | None,
    net_operating_assets: float | None,
) -> float | None:
    """RNOA (Penman). Caller must supply reformulated inputs: NOA = operating
    assets - operating liabilities, financing items excluded from both sides."""
    if net_operating_assets is not None and net_operating_assets <= 0:
        return None
    return _safe_div(after_tax_operating_income, net_operating_assets)


# ---------------------------------------------------------------------------
# Efficiency
# ---------------------------------------------------------------------------


def total_asset_turnover(revenue: float | None, avg_total_assets: float | None) -> float | None:
    if avg_total_assets is not None and avg_total_assets <= 0:
        return None
    return _safe_div(revenue, avg_total_assets)


def fixed_asset_turnover(revenue: float | None, avg_net_fixed_assets: float | None) -> float | None:
    if avg_net_fixed_assets is not None and avg_net_fixed_assets <= 0:
        return None
    return _safe_div(revenue, avg_net_fixed_assets)


def working_capital_turnover(revenue: float | None, avg_working_capital: float | None) -> float | None:
    """None when average working capital <= 0 (CFA: uninterpretable there)."""
    if avg_working_capital is not None and avg_working_capital <= 0:
        return None
    return _safe_div(revenue, avg_working_capital)


def days_inventory_on_hand(cogs: float | None, avg_inventory: float | None) -> float | None:
    if not _present(cogs, avg_inventory) or cogs <= 0 or avg_inventory <= 0:
        return None
    return DAYS_PER_YEAR / (cogs / avg_inventory)


def days_sales_outstanding(revenue: float | None, avg_receivables: float | None) -> float | None:
    if not _present(revenue, avg_receivables) or revenue <= 0 or avg_receivables <= 0:
        return None
    return DAYS_PER_YEAR / (revenue / avg_receivables)


def purchases(cogs: float | None, inventory_change: float | None) -> float | None:
    """Purchases ~= COGS + change in inventory (ending - beginning)."""
    if not _present(cogs, inventory_change):
        return None
    return cogs + inventory_change


def days_payables_outstanding(purchases: float | None, avg_payables: float | None) -> float | None:
    """Pass COGS as the accepted fallback when purchases can't be derived."""
    if not _present(purchases, avg_payables) or purchases <= 0 or avg_payables <= 0:
        return None
    return DAYS_PER_YEAR / (purchases / avg_payables)


def cash_conversion_cycle(
    days_inventory: float | None,
    days_sales: float | None,
    days_payables: float | None,
) -> float | None:
    """CCC = DIO + DSO - DPO. Negative means suppliers finance the operation."""
    if not _present(days_inventory, days_sales, days_payables):
        return None
    return days_inventory + days_sales - days_payables


# ---------------------------------------------------------------------------
# Liquidity
# ---------------------------------------------------------------------------


def current_ratio(current_assets: float | None, current_liabilities: float | None) -> float | None:
    if current_liabilities is not None and current_liabilities <= 0:
        return None
    return _safe_div(current_assets, current_liabilities)


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
    return _safe_div(
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
    return _safe_div(cash_and_equivalents + short_term_investments, current_liabilities)


def operating_cash_flow_ratio(cfo: float | None, current_liabilities: float | None) -> float | None:
    if current_liabilities is not None and current_liabilities <= 0:
        return None
    return _safe_div(cfo, current_liabilities)


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
    return _safe_div(total_debt, shareholders_equity)


def debt_to_assets(total_debt: float | None, total_assets: float | None) -> float | None:
    if total_assets is not None and total_assets <= 0:
        return None
    return _safe_div(total_debt, total_assets)


def debt_to_capital(total_debt: float | None, shareholders_equity: float | None) -> float | None:
    if not _present(total_debt, shareholders_equity):
        return None
    capital = total_debt + shareholders_equity
    if capital <= 0:
        return None
    return total_debt / capital


def financial_leverage(avg_total_assets: float | None, avg_total_equity: float | None) -> float | None:
    """Equity multiplier (assets / equity); the leverage leg of DuPont and the
    leverage measure that stays meaningful for banks."""
    if avg_total_equity is not None and avg_total_equity <= 0:
        return None
    return _safe_div(avg_total_assets, avg_total_equity)


def net_debt_to_ebitda(net_debt: float | None, ebitda: float | None) -> float | None:
    """None when EBITDA <= 0. A negative result means net cash."""
    if ebitda is not None and ebitda <= 0:
        return None
    return _safe_div(net_debt, ebitda)


def interest_coverage(ebit: float | None, interest_expense: float | None) -> float | None:
    """EBIT / gross interest expense. None when interest expense <= 0
    (no debt -> "not meaningful", per the reference doc)."""
    if interest_expense is not None and interest_expense <= 0:
        return None
    return _safe_div(ebit, interest_expense)


def ebitda_interest_coverage(ebitda: float | None, interest_expense: float | None) -> float | None:
    if interest_expense is not None and interest_expense <= 0:
        return None
    return _safe_div(ebitda, interest_expense)


def fixed_charge_coverage(
    ebit: float | None,
    lease_payments: float | None,
    interest_expense: float | None,
) -> float | None:
    if not _present(ebit, lease_payments, interest_expense):
        return None
    charges = interest_expense + lease_payments
    if charges <= 0:
        return None
    return (ebit + lease_payments) / charges


def cfo_to_debt(cfo: float | None, total_debt: float | None) -> float | None:
    if total_debt is not None and total_debt <= 0:
        return None
    return _safe_div(cfo, total_debt)


# ---------------------------------------------------------------------------
# Cash flow - generation & quality
# ---------------------------------------------------------------------------


def fcf_margin(fcf: float | None, revenue: float | None) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_div(fcf, revenue)


def cfo_to_net_income(cfo: float | None, net_income: float | None) -> float | None:
    """Earnings-quality check; persistently >= 1 is healthy. None when net
    income <= 0 (the ratio explodes near zero - use sloan_accruals_ratio)."""
    if net_income is not None and net_income <= 0:
        return None
    return _safe_div(cfo, net_income)


def sloan_accruals_ratio(
    net_income: float | None,
    cfo: float | None,
    cfi: float | None,
    total_assets: float | None,
) -> float | None:
    """(Net income - CFO - CFI) / total assets. Between -0.10 and +0.10 is
    considered safe; above +0.25 is a strong warning (Sloan 1996).
    ``cfi`` keeps its cash-flow-statement sign (usually negative)."""
    if not _present(net_income, cfo, cfi):
        return None
    if total_assets is None or total_assets <= 0:
        return None
    return (net_income - cfo - cfi) / total_assets


def fcf_conversion(fcf: float | None, ebitda: float | None) -> float | None:
    """FCF / EBITDA; >= 0.8 strong, ~1.0 ideal."""
    if ebitda is not None and ebitda <= 0:
        return None
    return _safe_div(fcf, ebitda)


def capex_intensity(capex: float | None, revenue: float | None) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_div(capex, revenue)


def capex_to_depreciation(capex: float | None, depreciation_amortization: float | None) -> float | None:
    """>1 growing asset base; <1 possible underinvestment (rough maintenance-
    capex proxy)."""
    if depreciation_amortization is not None and depreciation_amortization <= 0:
        return None
    return _safe_div(capex, depreciation_amortization)


# ---------------------------------------------------------------------------
# Growth
# ---------------------------------------------------------------------------


def growth_rate(current: float | None, prior: float | None) -> float | None:
    """Period-over-period growth. None when the base period is <= 0 (growth
    off a non-positive base is meaningless)."""
    if not _present(current, prior) or prior <= 0:
        return None
    return (current - prior) / prior


def cagr(latest: float | None, earliest: float | None, periods: float | None) -> float | None:
    """Compound annual growth rate over ``periods`` years."""
    if not _present(latest, earliest, periods) or earliest <= 0 or latest <= 0 or periods <= 0:
        return None
    return (latest / earliest) ** (1 / periods) - 1


def retention_rate(payout_ratio: float | None) -> float | None:
    if payout_ratio is None:
        return None
    return 1 - payout_ratio


def sustainable_growth_rate(roe: float | None, payout_ratio: float | None) -> float | None:
    """SGR = retention rate x ROE - growth fundable from retained earnings."""
    retention = retention_rate(payout_ratio)
    if not _present(roe, retention):
        return None
    return roe * retention


def reinvestment_rate(
    capex: float | None,
    depreciation_amortization: float | None,
    change_in_working_capital: float | None,
    nopat: float | None,
) -> float | None:
    """(Net capex + change in non-cash working capital) / NOPAT (Damodaran).
    None when NOPAT <= 0. Average over several years - capex is lumpy."""
    if not _present(capex, depreciation_amortization, change_in_working_capital):
        return None
    if nopat is None or nopat <= 0:
        return None
    return (capex - depreciation_amortization + change_in_working_capital) / nopat


def fundamental_growth(reinvestment_rate: float | None, roic: float | None) -> float | None:
    """Expected operating-income growth = reinvestment rate x ROIC."""
    if not _present(reinvestment_rate, roic):
        return None
    return reinvestment_rate * roic


# ---------------------------------------------------------------------------
# Valuation (market-cap form; see docs section 8 for the EV definition)
# ---------------------------------------------------------------------------


def price_to_earnings(market_cap: float | None, net_income: float | None) -> float | None:
    """Trailing P/E. None when earnings <= 0 (undefined; rank on
    earnings_yield instead)."""
    if net_income is not None and net_income <= 0:
        return None
    return _safe_div(market_cap, net_income)


def earnings_yield(net_income: float | None, market_cap: float | None) -> float | None:
    """E/P - defined even for negative earnings, so it ranks the full universe."""
    if market_cap is not None and market_cap <= 0:
        return None
    return _safe_div(net_income, market_cap)


def ebit_to_ev(ebit: float | None, enterprise_value: float | None) -> float | None:
    """Greenblatt's earnings yield: capital-structure-neutral E/P."""
    if enterprise_value is not None and enterprise_value <= 0:
        return None
    return _safe_div(ebit, enterprise_value)


def price_to_book(market_cap: float | None, common_equity: float | None) -> float | None:
    """None when book equity <= 0."""
    if common_equity is not None and common_equity <= 0:
        return None
    return _safe_div(market_cap, common_equity)


def price_to_sales(market_cap: float | None, revenue: float | None) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_div(market_cap, revenue)


def ev_to_ebitda(enterprise_value: float | None, ebitda: float | None) -> float | None:
    """None when EBITDA <= 0 (fall back to ev_to_sales)."""
    if ebitda is not None and ebitda <= 0:
        return None
    return _safe_div(enterprise_value, ebitda)


def ev_to_ebit(enterprise_value: float | None, ebit: float | None) -> float | None:
    if ebit is not None and ebit <= 0:
        return None
    return _safe_div(enterprise_value, ebit)


def ev_to_sales(enterprise_value: float | None, revenue: float | None) -> float | None:
    if revenue is not None and revenue <= 0:
        return None
    return _safe_div(enterprise_value, revenue)


def fcf_yield(fcf: float | None, market_cap: float | None) -> float | None:
    """FCF / market cap (equity form). P/FCF is its inverse."""
    if market_cap is not None and market_cap <= 0:
        return None
    return _safe_div(fcf, market_cap)


def dividend_yield(dividends_paid: float | None, market_cap: float | None) -> float | None:
    """Trailing-paid yield: common dividends paid (TTM) / market cap."""
    if market_cap is not None and market_cap <= 0:
        return None
    return _safe_div(dividends_paid, market_cap)


def payout_ratio(dividends_paid: float | None, net_income: float | None) -> float | None:
    """Dividends / net income. None when net income <= 0 (payout off losses
    is unsustainable by definition - compare dividends to FCF instead)."""
    if net_income is not None and net_income <= 0:
        return None
    return _safe_div(dividends_paid, net_income)


def shareholder_yield(
    dividends_paid: float | None,
    buybacks: float | None,
    stock_issued: float | None,
    market_cap: float | None,
) -> float | None:
    """(Dividends + buybacks - issuance) / market cap. Net of issuance so that
    buybacks merely offsetting stock-compensation dilution don't count."""
    if not _present(dividends_paid, buybacks, stock_issued):
        return None
    if market_cap is None or market_cap <= 0:
        return None
    return (dividends_paid + buybacks - stock_issued) / market_cap


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
    cfo: float | None,
    total_assets_begin: float | None,
    total_assets_begin_prior: float | None,
    long_term_debt: float | None,
    long_term_debt_prior: float | None,
    avg_total_assets: float | None,
    avg_total_assets_prior: float | None,
    current_assets: float | None,
    current_liabilities: float | None,
    current_assets_prior: float | None,
    current_liabilities_prior: float | None,
    revenue: float | None,
    revenue_prior: float | None,
    cogs: float | None,
    cogs_prior: float | None,
    common_stock_issued: float | None,
) -> FScoreResult:
    """Piotroski (2000) nine-signal score; see docs section 9.

    ``total_assets_begin`` is total assets at the *start* of the current year
    (== prior year-end); ``_prior`` variants are the same inputs one year
    earlier. ``common_stock_issued`` is the cash raised from common-stock
    issuance in the current year (0 or None-as-unknown; only an explicit 0
    earns the no-issuance point). Apply within cheap (high book-to-market)
    non-financial stocks, per the original paper.
    """
    roa = _safe_div(net_income, total_assets_begin) if (total_assets_begin or 0) > 0 else None
    roa_prior = (
        _safe_div(net_income_prior, total_assets_begin_prior)
        if (total_assets_begin_prior or 0) > 0
        else None
    )
    cfo_scaled = _safe_div(cfo, total_assets_begin) if (total_assets_begin or 0) > 0 else None

    leverage = _safe_div(long_term_debt, avg_total_assets)
    leverage_prior = _safe_div(long_term_debt_prior, avg_total_assets_prior)

    curr = current_ratio(current_assets, current_liabilities)
    curr_prior = current_ratio(current_assets_prior, current_liabilities_prior)

    margin = gross_profit_margin(gross_profit(revenue, cogs), revenue)
    margin_prior = gross_profit_margin(gross_profit(revenue_prior, cogs_prior), revenue_prior)

    turnover = _safe_div(revenue, total_assets_begin) if (total_assets_begin or 0) > 0 else None
    turnover_prior = (
        _safe_div(revenue_prior, total_assets_begin_prior)
        if (total_assets_begin_prior or 0) > 0
        else None
    )

    def _gt(a: float | None, b: float | None) -> bool | None:
        return None if not _present(a, b) else a > b

    def _lt(a: float | None, b: float | None) -> bool | None:
        return None if not _present(a, b) else a < b

    signals: dict[str, bool | None] = {
        "positive_roa": None if roa is None else roa > 0,
        "positive_cfo": None if cfo_scaled is None else cfo_scaled > 0,
        "improving_roa": _gt(roa, roa_prior),
        "cfo_exceeds_net_income": _gt(cfo, net_income),
        "decreasing_leverage": _lt(leverage, leverage_prior),
        "improving_current_ratio": _gt(curr, curr_prior),
        "no_stock_issuance": None if common_stock_issued is None else common_stock_issued <= 0,
        "improving_gross_margin": _gt(margin, margin_prior),
        "improving_asset_turnover": _gt(turnover, turnover_prior),
    }
    return FScoreResult(
        score=sum(1 for v in signals.values() if v is True),
        max_score=sum(1 for v in signals.values() if v is not None),
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
    ebit: float | None,
    market_cap: float | None,
    total_liabilities: float | None,
    revenue: float | None,
    total_assets: float | None,
) -> float | None:
    """Original Altman (1968) model for public manufacturers (SIC 2000-3999).
    Never apply to financials. Use altman_z_zone to interpret."""
    if not _present(working_capital, retained_earnings, ebit, market_cap, revenue):
        return None
    if not _present(total_liabilities, total_assets) or total_assets <= 0 or total_liabilities <= 0:
        return None
    return (
        1.2 * (working_capital / total_assets)
        + 1.4 * (retained_earnings / total_assets)
        + 3.3 * (ebit / total_assets)
        + 0.6 * (market_cap / total_liabilities)
        + 1.0 * (revenue / total_assets)
    )


def altman_z_zone(z: float | None) -> str | None:
    """Zones for the original model: safe > 2.99, distress < 1.81."""
    if z is None:
        return None
    if z > 2.99:
        return Z_SAFE
    if z < 1.81:
        return Z_DISTRESS
    return Z_GREY


def altman_z_double_prime(
    *,
    working_capital: float | None,
    retained_earnings: float | None,
    ebit: float | None,
    book_equity: float | None,
    total_liabilities: float | None,
    total_assets: float | None,
) -> float | None:
    """Z'' variant for non-manufacturers (drops asset turnover, book equity in
    X4). Never apply to financials. Use altman_z_double_prime_zone."""
    if not _present(working_capital, retained_earnings, ebit, book_equity):
        return None
    if not _present(total_liabilities, total_assets) or total_assets <= 0 or total_liabilities <= 0:
        return None
    return (
        6.56 * (working_capital / total_assets)
        + 3.26 * (retained_earnings / total_assets)
        + 6.72 * (ebit / total_assets)
        + 1.05 * (book_equity / total_liabilities)
    )


def altman_z_double_prime_zone(z: float | None) -> str | None:
    """Zones for Z'': safe > 2.6, distress < 1.1."""
    if z is None:
        return None
    if z > 2.6:
        return Z_SAFE
    if z < 1.1:
        return Z_DISTRESS
    return Z_GREY


# ---------------------------------------------------------------------------
# Composite: DuPont decomposition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DuPont3:
    net_margin: float
    asset_turnover: float
    equity_multiplier: float

    @property
    def roe(self) -> float:
        return self.net_margin * self.asset_turnover * self.equity_multiplier


@dataclass(frozen=True)
class DuPont5:
    tax_burden: float
    interest_burden: float
    ebit_margin: float
    asset_turnover: float
    equity_multiplier: float

    @property
    def roe(self) -> float:
        return (
            self.tax_burden
            * self.interest_burden
            * self.ebit_margin
            * self.asset_turnover
            * self.equity_multiplier
        )


def dupont_3(
    *,
    net_income: float | None,
    revenue: float | None,
    avg_total_assets: float | None,
    avg_total_equity: float | None,
) -> DuPont3 | None:
    """ROE = net margin x asset turnover x equity multiplier. High ROE from
    margin/turnover is operationally earned; from the multiplier, leverage-
    manufactured."""
    margin = net_profit_margin(net_income, revenue)
    turnover = total_asset_turnover(revenue, avg_total_assets)
    multiplier = financial_leverage(avg_total_assets, avg_total_equity)
    if not _present(margin, turnover, multiplier):
        return None
    return DuPont3(net_margin=margin, asset_turnover=turnover, equity_multiplier=multiplier)


def dupont_5(
    *,
    net_income: float | None,
    pretax_income: float | None,
    ebit: float | None,
    revenue: float | None,
    avg_total_assets: float | None,
    avg_total_equity: float | None,
) -> DuPont5 | None:
    """ROE = tax burden x interest burden x EBIT margin x asset turnover x
    equity multiplier. Uninterpretable (None) when pretax income or EBIT <= 0."""
    if not _present(pretax_income, ebit) or pretax_income <= 0 or ebit <= 0:
        return None
    tax_burden = _safe_div(net_income, pretax_income)
    interest_burden = pretax_income / ebit
    margin = operating_margin(ebit, revenue)
    turnover = total_asset_turnover(revenue, avg_total_assets)
    multiplier = financial_leverage(avg_total_assets, avg_total_equity)
    if not _present(tax_burden, margin, turnover, multiplier):
        return None
    return DuPont5(
        tax_burden=tax_burden,
        interest_burden=interest_burden,
        ebit_margin=margin,
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
    cogs: float
    receivables: float
    current_assets: float
    ppe_net: float
    total_assets: float
    depreciation: float
    sga_expense: float
    long_term_debt: float
    current_liabilities: float
    income_continuing_operations: float
    cfo: float


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

    def _index(num: float, den: float) -> float | None:
        return None if den == 0 else num / den

    def _receivable_days(p: BeneishPeriod) -> float | None:
        return _index(p.receivables, p.revenue)

    def _gross_margin(p: BeneishPeriod) -> float | None:
        return None if p.revenue == 0 else (p.revenue - p.cogs) / p.revenue

    def _soft_assets(p: BeneishPeriod) -> float | None:
        return None if p.total_assets == 0 else 1 - (p.current_assets + p.ppe_net) / p.total_assets

    def _dep_rate(p: BeneishPeriod) -> float | None:
        return _index(p.depreciation, p.depreciation + p.ppe_net)

    def _sga_ratio(p: BeneishPeriod) -> float | None:
        return _index(p.sga_expense, p.revenue)

    def _leverage(p: BeneishPeriod) -> float | None:
        return _index(p.long_term_debt + p.current_liabilities, p.total_assets)

    pairs = {
        "dsri": (_receivable_days(current), _receivable_days(prior)),
        "gmi": (_gross_margin(prior), _gross_margin(current)),  # prior over current
        "aqi": (_soft_assets(current), _soft_assets(prior)),
        "sgi": (current.revenue, prior.revenue),
        "depi": (_dep_rate(prior), _dep_rate(current)),  # prior over current
        "sgai": (_sga_ratio(current), _sga_ratio(prior)),
        "lvgi": (_leverage(current), _leverage(prior)),
    }
    indices: dict[str, float] = {}
    for name, (num, den) in pairs.items():
        ratio = None if not _present(num, den) else _index(num, den)
        if ratio is None:
            return None
        indices[name] = ratio

    if current.total_assets == 0:
        return None
    indices["tata"] = (
        current.income_continuing_operations - current.cfo
    ) / current.total_assets

    m = (
        -4.840
        + 0.920 * indices["dsri"]
        + 0.528 * indices["gmi"]
        + 0.404 * indices["aqi"]
        + 0.892 * indices["sgi"]
        + 0.115 * indices["depi"]
        - 0.172 * indices["sgai"]
        - 0.327 * indices["lvgi"]
        + 4.679 * indices["tata"]
    )
    return BeneishResult(m_score=m, indices=indices)
