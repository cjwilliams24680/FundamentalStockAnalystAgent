"""Raw values agents must parse from a quarterly report to feed the
calculation functions in :mod:`metrics`.

:class:`QuarterlyReportParseResult` enumerates every leaf input consumed by
the functions in ``metrics.py`` — the values that come straight off the three
financial statements. Field descriptions are written for the parsing agent:
where the value appears in a quarterly report and the synonym labels filers
use for it. Notes about how a field maps onto ``metrics.py`` parameters are
kept in code comments instead. It deliberately excludes:

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
"""

from pydantic import BaseModel, ConfigDict, Field


class QuarterlyReportParseResult(BaseModel):
    """Every raw statement value needed by the functions in ``metrics.py``,
    for a single reporting period."""

    model_config = ConfigDict(frozen=True)

    # ------------------------------------------------------------------
    # Income statement
    # ------------------------------------------------------------------

    revenue: float | None = Field(
        default=None,
        description=(
            "Top line of the income statement. Labeled 'Revenue', 'Net"
            " sales', 'Total revenues', 'Net revenues', or 'Sales'. If"
            " product and service revenue are listed separately, use the"
            " total."
        ),
    )
    cost_of_goods_sold: float | None = Field(
        default=None,
        description=(
            "Income statement line directly below revenue. Labeled 'Cost of"
            " goods sold', 'Cost of sales', 'Cost of revenue', or 'Cost of"
            " products sold'."
        ),
    )
    # Feeds every ``operating_income`` and ``earnings_before_interest_and_taxes``
    # parameter in metrics.py (they are the same figure).
    operating_income: float | None = Field(
        default=None,
        description=(
            "Income statement subtotal after operating expenses. Labeled"
            " 'Operating income', 'Income from operations', or 'Operating"
            " profit'."
        ),
    )
    pretax_income: float | None = Field(
        default=None,
        description=(
            "Income statement line just above the tax provision. Labeled"
            " 'Income before income taxes', 'Income before provision for"
            " income taxes', 'Earnings before income taxes', or 'Pre-tax"
            " income'."
        ),
    )
    income_tax_expense: float | None = Field(
        default=None,
        description=(
            "Income statement line between pretax income and net income."
            " Labeled 'Provision for income taxes', 'Income tax provision',"
            " or 'Income tax expense (benefit)'."
        ),
    )
    net_income: float | None = Field(
        default=None,
        description=(
            "Bottom line of the income statement. Labeled 'Net income' or"
            " 'Net earnings'. When noncontrolling interests are present, use"
            " the line 'Net income attributable to [company]', not the"
            " consolidated total."
        ),
    )
    # BeneishPeriod.income_from_continuing_operations.
    income_from_continuing_operations: float | None = Field(
        default=None,
        description=(
            "Income statement line above any discontinued-operations items."
            " Labeled 'Income from continuing operations' (often 'net of"
            " tax'). Equals net income when the filing shows no discontinued"
            " operations."
        ),
    )
    interest_expense: float | None = Field(
        default=None,
        description=(
            "Non-operating section of the income statement, or the debt note."
            " Labeled 'Interest expense'. Prefer the gross figure; filings"
            " that only show 'Interest expense, net' or 'Other income"
            " (expense), net' may break out the gross amount in the notes."
        ),
    )
    # defensive_interval_ratio input.
    operating_expenses: float | None = Field(
        default=None,
        description=(
            "Income statement subtotal of all operating costs. Labeled"
            " 'Total operating expenses' or 'Total costs and expenses'."
        ),
    )
    # BeneishPeriod.selling_general_and_administrative_expense.
    selling_general_and_administrative_expense: float | None = Field(
        default=None,
        description=(
            "Operating expense line of the income statement. Labeled"
            " 'Selling, general and administrative' (commonly abbreviated"
            " SG&A). If shown as separate 'Selling and marketing' and"
            " 'General and administrative' lines, use their sum."
        ),
    )
    preferred_dividends: float | None = Field(
        default=None,
        description=(
            "Below net income on the income statement or in the statement of"
            " stockholders' equity. Labeled 'Preferred stock dividends' or"
            " 'Dividends on preferred stock'. Usually absent — most companies"
            " have no preferred stock outstanding."
        ),
    )
    weighted_average_shares: float | None = Field(
        default=None,
        description=(
            "Bottom of the income statement, near the per-share figures."
            " Labeled 'Weighted-average shares outstanding' or"
            " 'Weighted-average number of common shares' (basic). A share"
            " count, not a currency amount."
        ),
    )

    # ------------------------------------------------------------------
    # Cash flow statement
    # ------------------------------------------------------------------

    operating_cash_flow: float | None = Field(
        default=None,
        description=(
            "Subtotal of the cash flow statement's operating section. Labeled"
            " 'Net cash provided by operating activities', 'Cash flows from"
            " operating activities', or 'Net cash generated by operating"
            " activities'."
        ),
    )
    # sloan_accruals_ratio input; keeps its cash-flow-statement sign.
    investing_cash_flow: float | None = Field(
        default=None,
        description=(
            "Subtotal of the cash flow statement's investing section. Labeled"
            " 'Net cash used in investing activities' or 'Cash flows from"
            " investing activities'. Keep the sign as reported (usually"
            " negative)."
        ),
    )
    depreciation_and_amortization: float | None = Field(
        default=None,
        description=(
            "Adjustment near the top of the cash flow statement's operating"
            " section. Labeled 'Depreciation and amortization' (commonly"
            " abbreviated D&A). If depreciation and amortization appear as"
            " separate lines, use their sum."
        ),
    )
    # BeneishPeriod.depreciation — depreciation alone, excluding amortization.
    depreciation: float | None = Field(
        default=None,
        description=(
            "Depreciation expense excluding amortization. Found in the cash"
            " flow statement when shown as its own line, or in the property,"
            " plant and equipment note. Leave unset when the filing only"
            " reports a combined depreciation-and-amortization figure."
        ),
    )
    # defensive_interval_ratio input.
    non_cash_charges: float | None = Field(
        default=None,
        description=(
            "Sum of the non-cash adjustment lines in the cash flow"
            " statement's operating section: depreciation and amortization,"
            " stock-based compensation, impairments, deferred income taxes,"
            " and similar items (exclude working-capital changes)."
        ),
    )
    capital_expenditures: float | None = Field(
        default=None,
        description=(
            "Investing section of the cash flow statement. Labeled 'Purchases"
            " of property, plant and equipment', 'Payments for property and"
            " equipment', 'Additions to property and equipment', or 'Capital"
            " expenditures'. Record as a positive amount."
        ),
    )
    dividends_paid: float | None = Field(
        default=None,
        description=(
            "Financing section of the cash flow statement. Labeled 'Dividends"
            " paid', 'Payments of dividends', or 'Cash dividends paid'. Use"
            " the common-stock amount when preferred dividends are listed"
            " separately. Record as a positive amount."
        ),
    )
    # shareholder_yield's ``buybacks``.
    buybacks: float | None = Field(
        default=None,
        description=(
            "Financing section of the cash flow statement. Labeled"
            " 'Repurchases of common stock', 'Payments for repurchase of"
            " common stock', or 'Purchases of treasury stock'. Record as a"
            " positive amount."
        ),
    )
    # Feeds shareholder_yield's ``stock_issued`` and piotroski_f_score's
    # ``common_stock_issued``.
    common_stock_issued: float | None = Field(
        default=None,
        description=(
            "Financing section of the cash flow statement. Labeled 'Proceeds"
            " from issuance of common stock', often including 'Proceeds from"
            " exercise of stock options' or 'employee stock purchase plan'"
            " lines — sum them. Record as a positive amount."
        ),
    )

    # ------------------------------------------------------------------
    # Balance sheet
    # ------------------------------------------------------------------

    cash_and_equivalents: float | None = Field(
        default=None,
        description=(
            "First line of the balance sheet's current assets. Labeled 'Cash"
            " and cash equivalents'. Exclude restricted cash and short-term"
            " investments shown on separate lines."
        ),
    )
    # Feeds the liquidity ratios' ``short_term_investments`` and net_debt's
    # ``marketable_securities`` (the same line item).
    short_term_investments: float | None = Field(
        default=None,
        description=(
            "Current assets section of the balance sheet, next to cash."
            " Labeled 'Short-term investments', 'Marketable securities', or"
            " 'Short-term marketable securities'."
        ),
    )
    receivables: float | None = Field(
        default=None,
        description=(
            "Current assets section of the balance sheet. Labeled 'Accounts"
            " receivable, net', 'Trade receivables', or 'Receivables, net'."
        ),
    )
    inventory: float | None = Field(
        default=None,
        description=(
            "Current assets section of the balance sheet. Labeled"
            " 'Inventories', 'Inventory', or 'Inventories, net'."
        ),
    )
    current_assets: float | None = Field(
        default=None,
        description=(
            "Balance sheet subtotal. Labeled 'Total current assets'."
        ),
    )
    # Feeds ``average_net_fixed_assets`` (via metrics.average) and
    # BeneishPeriod.net_property_plant_and_equipment.
    net_property_plant_and_equipment: float | None = Field(
        default=None,
        description=(
            "Non-current assets section of the balance sheet. Labeled"
            " 'Property, plant and equipment, net' or 'Property and"
            " equipment, net' — the figure after accumulated depreciation."
        ),
    )
    # Also the source of ``beginning_total_assets`` when this instance is the
    # prior period.
    total_assets: float | None = Field(
        default=None,
        description="Balance sheet subtotal. Labeled 'Total assets'.",
    )
    # total_debt input.
    short_term_debt: float | None = Field(
        default=None,
        description=(
            "Interest-bearing borrowings in the balance sheet's current"
            " liabilities. Labeled 'Short-term borrowings', 'Short-term"
            " debt', 'Commercial paper', 'Notes payable', or 'Current portion"
            " of long-term debt' — sum all such lines. Exclude accounts"
            " payable and accrued liabilities."
        ),
    )
    long_term_debt: float | None = Field(
        default=None,
        description=(
            "Non-current liabilities section of the balance sheet. Labeled"
            " 'Long-term debt', 'Long-term borrowings', or 'Senior notes' —"
            " the portion due beyond one year."
        ),
    )
    # total_debt input.
    lease_obligations: float | None = Field(
        default=None,
        description=(
            "Balance sheet liability lines labeled 'Operating lease"
            " liabilities' and 'Finance lease liabilities' — sum the current"
            " and non-current portions. Exclude any lease amounts already"
            " counted in short-term or long-term debt."
        ),
    )
    # Combine two periods for ``average_payables`` (days_payables_outstanding).
    payables: float | None = Field(
        default=None,
        description=(
            "Current liabilities section of the balance sheet. Labeled"
            " 'Accounts payable' or 'Trade payables'."
        ),
    )
    current_liabilities: float | None = Field(
        default=None,
        description=(
            "Balance sheet subtotal. Labeled 'Total current liabilities'."
        ),
    )
    # altman_z_score / altman_z_double_prime input.
    total_liabilities: float | None = Field(
        default=None,
        description=(
            "Balance sheet subtotal. Labeled 'Total liabilities'. If not"
            " shown explicitly, it is 'Total liabilities and stockholders'"
            " equity' minus total equity."
        ),
    )
    # altman_z_score / altman_z_double_prime input.
    retained_earnings: float | None = Field(
        default=None,
        description=(
            "Stockholders' equity section of the balance sheet. Labeled"
            " 'Retained earnings', 'Accumulated deficit' (a negative"
            " retained-earnings balance), or 'Reinvested earnings'."
        ),
    )
    # enterprise_value input; also subtracted from shareholders_equity to form
    # the ``common_equity`` / ``book_equity`` inputs.
    preferred_equity: float | None = Field(
        default=None,
        description=(
            "Stockholders' equity section of the balance sheet. Labeled"
            " 'Preferred stock'. Usually zero or absent — most companies have"
            " none outstanding."
        ),
    )
    # enterprise_value input.
    minority_interest: float | None = Field(
        default=None,
        description=(
            "Equity section of the balance sheet. Labeled 'Noncontrolling"
            " interests' or 'Minority interest' — the equity of consolidated"
            " subsidiaries not owned by the parent."
        ),
    )
    # The ``common_equity`` / ``book_equity`` inputs (price_to_book,
    # altman_z_double_prime) are ``shareholders_equity - preferred_equity``.
    shareholders_equity: float | None = Field(
        default=None,
        description=(
            "Balance sheet subtotal. Labeled 'Total stockholders' equity',"
            " 'Total shareholders' equity', or 'Total equity'. When"
            " noncontrolling interests are present, use the amount"
            " attributable to the parent company."
        ),
    )
