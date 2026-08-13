"""Raw values agents must parse from a quarterly report to feed the
calculation functions in :mod:`metrics`.

:class:`QuarterlyReportParseResult` enumerates every leaf input consumed by
the functions in ``metrics.py`` — the values that come straight off the three
financial statements. It deliberately excludes:

- Intermediates that ``metrics.py`` already computes from these fields
  (``gross_profit``, ``total_debt``, ``net_debt``, ``working_capital``,
  ``invested_capital``, ``enterprise_value``, ``free_cash_flow``, earnings
  before interest, taxes, depreciation, and amortization, net operating
  profit after tax, ``purchases``, ``effective_tax_rate``, ...).
- ``market_capitalization`` — market data, not parseable from a filing;
  callers wire it in separately.
- ``average_...``, ``..._prior``, and change-across-periods inputs
  (``inventory_change``, ``change_in_working_capital``, the Piotroski and
  Beneish prior-year values). One instance represents one reporting period;
  build those inputs by combining the current instance with one parsed from
  an earlier report (using :func:`metrics.average` for average balances).

Conventions match ``metrics.py``: absolute amounts in the filing's currency
(not per-share); every field defaults to ``None`` meaning the value was not
reported (mirroring the gaps in real XBRL data); capital expenditures,
dividends paid, buybacks, and stock issuance are positive magnitudes with the
cash-flow-statement sign stripped, while ``investing_cash_flow`` keeps its
statement sign (usually negative).

Where ``metrics.py`` uses near-duplicate parameter names for the same
statement line item, this class has a single unified field; each field's
comment maps it to the parameter names it feeds.
"""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class QuarterlyReportParseResult:
    """Every raw statement value needed by the functions in ``metrics.py``,
    for a single reporting period."""

    # ------------------------------------------------------------------
    # Income statement
    # ------------------------------------------------------------------

    revenue: float | None = None
    cost_of_goods_sold: float | None = None
    # Feeds every ``operating_income`` / ``earnings_before_interest_and_taxes``
    # parameter (they are the same figure in metrics.py).
    operating_income: float | None = None
    pretax_income: float | None = None
    income_tax_expense: float | None = None
    net_income: float | None = None
    income_from_continuing_operations: float | None = None
    interest_expense: float | None = None
    operating_expenses: float | None = None
    selling_general_and_administrative_expense: float | None = None
    preferred_dividends: float | None = None
    weighted_average_shares: float | None = None

    # ------------------------------------------------------------------
    # Cash flow statement
    # ------------------------------------------------------------------

    operating_cash_flow: float | None = None
    # Keeps its cash-flow-statement sign (usually negative).
    investing_cash_flow: float | None = None
    depreciation_and_amortization: float | None = None
    # Depreciation alone, excluding amortization (BeneishPeriod.depreciation).
    depreciation: float | None = None
    non_cash_charges: float | None = None
    capital_expenditures: float | None = None
    dividends_paid: float | None = None
    buybacks: float | None = None
    # Cash raised from common-stock issuance; feeds shareholder_yield's
    # ``stock_issued`` and piotroski_f_score's ``common_stock_issued``.
    common_stock_issued: float | None = None

    # ------------------------------------------------------------------
    # Balance sheet
    # ------------------------------------------------------------------

    cash_and_equivalents: float | None = None
    # Feeds the liquidity ratios' ``short_term_investments`` and net_debt's
    # ``marketable_securities`` (the same line item).
    short_term_investments: float | None = None
    receivables: float | None = None
    inventory: float | None = None
    current_assets: float | None = None
    # Feeds ``average_net_fixed_assets`` (via metrics.average) and
    # BeneishPeriod.net_property_plant_and_equipment.
    net_property_plant_and_equipment: float | None = None
    total_assets: float | None = None
    short_term_debt: float | None = None
    long_term_debt: float | None = None
    lease_obligations: float | None = None
    payables: float | None = None
    current_liabilities: float | None = None
    total_liabilities: float | None = None
    retained_earnings: float | None = None
    preferred_equity: float | None = None
    minority_interest: float | None = None
    # Total shareholders' equity. The ``common_equity`` / ``book_equity``
    # inputs (price_to_book, altman_z_double_prime) are
    # ``shareholders_equity - preferred_equity``.
    shareholders_equity: float | None = None
