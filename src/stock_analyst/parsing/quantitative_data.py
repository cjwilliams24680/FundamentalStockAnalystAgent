"""Raw values agents must parse from a quarterly report to feed the
calculation functions in :mod:`calculations`.

:class:`RawQuantitativeData` enumerates every leaf input consumed by
the functions in ``calculations.py`` — the values that come straight off the
three financial statements. Field descriptions are written for the parsing
agent: where the value appears in a quarterly report and the synonym labels
filers use for it. Notes about how a field maps onto ``calculations.py``
parameters are kept in code comments instead. It deliberately excludes:

- Intermediates that ``calculations.py`` already computes from these fields
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
  an earlier report (using :func:`calculations.average` for average balances).

One instance covers one reporting period measured fiscal-year-to-date: every
flow value (income statement and cash flow statement) runs from the start of
the fiscal year through the balance sheet date. Parse the year-to-date
column — labeled 'Three/Six/Nine months ended' or
'Thirteen/Twenty-six/Thirty-nine weeks ended' depending on the quarter —
never the single-quarter column; in a first-quarter filing the two coincide.
The cash flow statement is only presented year-to-date, so this is the only
period for which one filing provides a complete, consistent set of flows;
true single-quarter flows are a multi-period derivation (differencing
consecutive parse results), like the other multi-period inputs excluded
above. Balance-sheet values are point-in-time as of the period end.

Conventions match ``calculations.py``: absolute amounts in the filing's currency
(not per-share); every field defaults to ``None`` meaning the value was not
reported (mirroring the gaps in real XBRL data); capital expenditures,
dividends paid, buybacks, and stock issuance are positive magnitudes with the
cash-flow-statement sign stripped, while ``investing_cash_flow`` keeps its
statement sign (usually negative).

The "absolute amounts" convention is implemented in two steps: the parsing
agent records numbers exactly as printed (filings state a scale such as
'(In millions)'), and the pipeline multiplies each table's parse result by
its stated scale (``table_parser.FinancialStatementUnitScale``) via
:meth:`RawQuantitativeData.apply_unit_scale` before merging — so a
populated instance holds whole currency units. Flows remain fiscal-year-to-
date here; annualizing them to a run rate for metric comparability is
``run_all_calculations``' responsibility, via
:meth:`RawQuantitativeData.annualize_year_to_date_flow_values`. The
module-level frozensets (``YEAR_TO_DATE_FLOW_FIELD_NAMES``,
``BALANCE_SHEET_FIELD_NAMES``, ``SHARE_COUNT_FIELD_NAMES``) classify every
field for those transformations and must partition the model exactly.
"""

from pydantic import BaseModel, ConfigDict, Field

# Every field is one of these three kinds; tests assert the sets partition
# ``model_fields`` exactly, so any new field must be classified here.
YEAR_TO_DATE_FLOW_FIELD_NAMES = frozenset(
    {
        # Income statement
        "revenue",
        "cost_of_goods_sold",
        "operating_income",
        "pretax_income",
        "income_tax_expense",
        "net_income",
        "income_from_continuing_operations",
        "interest_expense",
        "operating_expenses",
        "selling_general_and_administrative_expense",
        "preferred_dividends",
        # Cash flow statement
        "operating_cash_flow",
        "investing_cash_flow",
        "depreciation_and_amortization",
        "depreciation",
        "non_cash_charges",
        "capital_expenditures",
        "dividends_paid",
        "buybacks",
        "common_stock_issued",
    }
)

BALANCE_SHEET_FIELD_NAMES = frozenset(
    {
        "cash_and_equivalents",
        "short_term_investments",
        "receivables",
        "inventory",
        "current_assets",
        "net_property_plant_and_equipment",
        "total_assets",
        "short_term_debt",
        "long_term_debt",
        "lease_obligations",
        "payables",
        "current_liabilities",
        "total_liabilities",
        "retained_earnings",
        "preferred_equity",
        "minority_interest",
        "shareholders_equity",
    }
)

SHARE_COUNT_FIELD_NAMES = frozenset({"weighted_average_diluted_shares"})

_ANNUALIZATION_FACTOR_BY_FISCAL_QUARTER = {
    "Q1": 4.0,
    "Q2": 2.0,
    "Q3": 4.0 / 3.0,
    "Q4": 1.0,
}


class RawQuantitativeData(BaseModel):
    """Every raw statement value needed by the functions in ``calculations.py``,
    for a single reporting period."""

    model_config = ConfigDict(frozen=True)

    def merge(self, other: "RawQuantitativeData") -> "RawQuantitativeData":
        """Combine two parse results, preferring this instance's values.

        For each field, uses this instance's value when it is not ``None``,
        otherwise falls back to ``other``'s value.
        """
        merged_field_values = {
            field_name: (
                getattr(self, field_name)
                if getattr(self, field_name) is not None
                else getattr(other, field_name)
            )
            for field_name in type(self).model_fields
        }
        return RawQuantitativeData(**merged_field_values)

    def apply_unit_scale(
        self, monetary_value_multiplier: float, share_count_multiplier: float
    ) -> "RawQuantitativeData":
        """Convert values recorded as printed into whole currency units.

        Filings print amounts at a stated scale (e.g. '(In millions)'); the
        parsing agent records numbers exactly as printed, and this method
        multiplies them out deterministically. Monetary fields use
        ``monetary_value_multiplier``; share-count fields use
        ``share_count_multiplier`` (equal to the monetary one under the
        common 'except per share data' caption, 1.0 when the caption
        excludes share amounts from the scale). ``None`` stays ``None``.
        """
        scaled_field_values = {}
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if value is None:
                scaled_field_values[field_name] = None
            elif field_name in SHARE_COUNT_FIELD_NAMES:
                scaled_field_values[field_name] = value * share_count_multiplier
            else:
                scaled_field_values[field_name] = value * monetary_value_multiplier
        return RawQuantitativeData(**scaled_field_values)

    def annualize_year_to_date_flow_values(
        self, fiscal_quarter: str
    ) -> "RawQuantitativeData":
        """Scale fiscal-year-to-date flows to a run-rate annual figure.

        Multiplies the income statement and cash flow statement fields by
        4 / quarter number (Q1 x4, Q2 x2, Q3 x4/3, Q4 x1) so metrics that
        compare a flow against a balance-sheet stock or market
        capitalization are comparable to annual reference bands.
        Balance-sheet fields are point-in-time and stay untouched, as does
        ``weighted_average_diluted_shares`` (a period average, not a
        cumulative flow). Raises ``ValueError`` for an unknown quarter.
        """
        if fiscal_quarter not in _ANNUALIZATION_FACTOR_BY_FISCAL_QUARTER:
            raise ValueError(f"Invalid fiscal quarter: {fiscal_quarter}")
        annualization_factor = _ANNUALIZATION_FACTOR_BY_FISCAL_QUARTER[fiscal_quarter]
        annualized_field_values = {}
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if value is not None and field_name in YEAR_TO_DATE_FLOW_FIELD_NAMES:
                value = value * annualization_factor
            annualized_field_values[field_name] = value
        return RawQuantitativeData(**annualized_field_values)

    # ------------------------------------------------------------------
    # Income statement
    # ------------------------------------------------------------------

    revenue: float | None = Field(
        default=None,
        description=(
            "Top line of the income statement. Labeled 'Revenue', 'Net"
            " sales', 'Total revenues', 'Net revenues', or 'Sales'. If"
            " product and service revenue are listed separately, use the"
            " total. Use the year-to-date column (e.g. 'Six months ended' or"
            " 'Thirty-nine weeks ended'), not the single-quarter column."
        ),
    )
    cost_of_goods_sold: float | None = Field(
        default=None,
        description=(
            "Income statement line directly below revenue. Labeled 'Cost of"
            " goods sold', 'Cost of sales', 'Cost of revenue', or 'Cost of"
            " products sold'. Use the year-to-date column (e.g. 'Six months"
            " ended' or 'Thirty-nine weeks ended'), not the single-quarter"
            " column."
        ),
    )
    # Feeds every ``operating_income`` and ``earnings_before_interest_and_taxes``
    # parameter in calculations.py (they are the same figure).
    operating_income: float | None = Field(
        default=None,
        description=(
            "Income statement subtotal after operating expenses. Labeled"
            " 'Operating income', 'Income from operations', or 'Operating"
            " profit'. Use the year-to-date column (e.g. 'Six months ended'"
            " or 'Thirty-nine weeks ended'), not the single-quarter column."
        ),
    )
    pretax_income: float | None = Field(
        default=None,
        description=(
            "Income statement line just above the tax provision. Labeled"
            " 'Income before income taxes', 'Income before provision for"
            " income taxes', 'Earnings before income taxes', or 'Pre-tax"
            " income'. Use the year-to-date column (e.g. 'Six months ended'"
            " or 'Thirty-nine weeks ended'), not the single-quarter column."
        ),
    )
    income_tax_expense: float | None = Field(
        default=None,
        description=(
            "Income statement line between pretax income and net income."
            " Labeled 'Provision for income taxes', 'Income tax provision',"
            " or 'Income tax expense (benefit)'. Use the year-to-date column"
            " (e.g. 'Six months ended' or 'Thirty-nine weeks ended'), not the"
            " single-quarter column."
        ),
    )
    net_income: float | None = Field(
        default=None,
        description=(
            "Bottom line of the income statement. Labeled 'Net income' or"
            " 'Net earnings'. When noncontrolling interests are present, use"
            " the line 'Net income attributable to [company]', not the"
            " consolidated total. Use the year-to-date column (e.g. 'Six"
            " months ended' or 'Thirty-nine weeks ended'), not the"
            " single-quarter column."
        ),
    )
    # BeneishPeriod.income_from_continuing_operations.
    income_from_continuing_operations: float | None = Field(
        default=None,
        description=(
            "Income statement line above any discontinued-operations items."
            " Labeled 'Income from continuing operations' (often 'net of"
            " tax'). Equals net income when the filing shows no discontinued"
            " operations. Use the year-to-date column (e.g. 'Six months"
            " ended' or 'Thirty-nine weeks ended'), not the single-quarter"
            " column."
        ),
    )
    interest_expense: float | None = Field(
        default=None,
        description=(
            "Non-operating section of the income statement, or the debt note."
            " Labeled 'Interest expense'. Prefer the gross figure; filings"
            " that only show 'Interest expense, net' or 'Other income"
            " (expense), net' may break out the gross amount in the notes."
            " Use the year-to-date amount (e.g. 'Six months ended' or"
            " 'Thirty-nine weeks ended'), not the single-quarter amount."
        ),
    )
    # defensive_interval_ratio input.
    operating_expenses: float | None = Field(
        default=None,
        description=(
            "Income statement subtotal of all operating costs. Labeled"
            " 'Total operating expenses' or 'Total costs and expenses'. Use"
            " the year-to-date column (e.g. 'Six months ended' or"
            " 'Thirty-nine weeks ended'), not the single-quarter column."
        ),
    )
    # BeneishPeriod.selling_general_and_administrative_expense.
    selling_general_and_administrative_expense: float | None = Field(
        default=None,
        description=(
            "Operating expense line of the income statement. Labeled"
            " 'Selling, general and administrative' (commonly abbreviated"
            " SG&A). If shown as separate 'Selling and marketing' and"
            " 'General and administrative' lines, use their sum. Use the"
            " year-to-date column (e.g. 'Six months ended' or 'Thirty-nine"
            " weeks ended'), not the single-quarter column."
        ),
    )
    preferred_dividends: float | None = Field(
        default=None,
        description=(
            "Below net income on the income statement or in the statement of"
            " stockholders' equity. Labeled 'Preferred stock dividends' or"
            " 'Dividends on preferred stock'. Usually absent — most companies"
            " have no preferred stock outstanding. Use the year-to-date"
            " amount, not the single-quarter amount."
        ),
    )
    weighted_average_diluted_shares: float | None = Field(
        default=None,
        description=(
            "Bottom of the income statement, near the per-share figures."
            " Labeled 'Weighted-average shares outstanding — diluted' or"
            " 'Weighted-average number of common shares, diluted'. Use the"
            " diluted count, not the basic one (in a loss period filers"
            " report diluted equal to basic, so the diluted line always"
            " exists). A share count, not a currency amount. Use the"
            " year-to-date column's weighted average, not the single-quarter"
            " figure."
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
            " activities'. Year-to-date, as the cash flow statement presents"
            " it."
        ),
    )
    # sloan_accruals_ratio input; keeps its cash-flow-statement sign.
    investing_cash_flow: float | None = Field(
        default=None,
        description=(
            "Subtotal of the cash flow statement's investing section. Labeled"
            " 'Net cash used in investing activities' or 'Cash flows from"
            " investing activities'. Keep the sign as reported (usually"
            " negative). Year-to-date, as the cash flow statement presents"
            " it."
        ),
    )
    depreciation_and_amortization: float | None = Field(
        default=None,
        description=(
            "Adjustment near the top of the cash flow statement's operating"
            " section. Labeled 'Depreciation and amortization' (commonly"
            " abbreviated D&A). If depreciation and amortization appear as"
            " separate lines, use their sum. Use the year-to-date amount from"
            " the cash flow statement; when a note or supplementary schedule"
            " shows both a single-quarter and a year-to-date figure, take the"
            " year-to-date one."
        ),
    )
    # BeneishPeriod.depreciation — depreciation alone, excluding amortization.
    depreciation: float | None = Field(
        default=None,
        description=(
            "Depreciation expense excluding amortization. Found in the cash"
            " flow statement when shown as its own line, or in the property,"
            " plant and equipment note. Leave unset when the filing only"
            " reports a combined depreciation-and-amortization figure. Use"
            " the year-to-date figure, not the single-quarter one."
        ),
    )
    # defensive_interval_ratio input.
    non_cash_charges: float | None = Field(
        default=None,
        description=(
            "Sum of the non-cash adjustment lines in the cash flow"
            " statement's operating section: depreciation and amortization,"
            " stock-based compensation, impairments, deferred income taxes,"
            " and similar items (exclude working-capital changes). Sum the"
            " year-to-date amounts, as the cash flow statement presents them."
        ),
    )
    capital_expenditures: float | None = Field(
        default=None,
        description=(
            "Investing section of the cash flow statement. Labeled 'Purchases"
            " of property, plant and equipment', 'Payments for property and"
            " equipment', 'Additions to property and equipment', or 'Capital"
            " expenditures'. Record the year-to-date amount as a positive"
            " number."
        ),
    )
    dividends_paid: float | None = Field(
        default=None,
        description=(
            "Financing section of the cash flow statement. Labeled 'Dividends"
            " paid', 'Payments of dividends', or 'Cash dividends paid'. Use"
            " the common-stock amount when preferred dividends are listed"
            " separately. Record the year-to-date amount as a positive"
            " number."
        ),
    )
    # shareholder_yield's ``buybacks``.
    buybacks: float | None = Field(
        default=None,
        description=(
            "Financing section of the cash flow statement. Labeled"
            " 'Repurchases of common stock', 'Payments for repurchase of"
            " common stock', or 'Purchases of treasury stock'. Record the"
            " year-to-date amount as a positive number."
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
            " lines — sum them. Record the year-to-date amount as a positive"
            " number."
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
        description=("Balance sheet subtotal. Labeled 'Total current assets'."),
    )
    # Feeds ``average_net_fixed_assets`` (via calculations.average) and
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
        description=("Balance sheet subtotal. Labeled 'Total current liabilities'."),
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


def get_diffs(first: RawQuantitativeData, second: RawQuantitativeData) -> list[str]:
    """Describe every field whose value differs between ``first`` and
    ``second``, one string per differing field. Equal instances yield an
    empty list."""
    diffs = []
    for field_name in RawQuantitativeData.model_fields:
        first_value = getattr(first, field_name)
        second_value = getattr(second, field_name)
        if first_value != second_value:
            diffs.append(f"{field_name}: {first_value} != {second_value}")
    return diffs


def count_populated_fields(parse_result: RawQuantitativeData) -> int:
    """Number of fields on ``parse_result`` that are not ``None``."""
    return sum(
        getattr(parse_result, field_name) is not None
        for field_name in RawQuantitativeData.model_fields
    )
