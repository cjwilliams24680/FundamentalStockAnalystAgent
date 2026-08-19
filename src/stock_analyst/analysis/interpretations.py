"""Read each :class:`calculated_metrics.CalculatedValues` field into plain
language for interpretation agents.

One ``interpret_<field_name>`` function per field;
``calculation_interpreter.py`` runs all of them in the model's declaration
order. The reference bands come from the ``CalculatedValues``
field descriptions, which distill ``docs/fundamental_metrics.md`` — that doc
remains the authority when a band here needs justification.

Conventions:

- Every interpreter accepts ``None`` and still returns a
  :class:`CalculationInterpretation`. ``None`` never sets
  ``falls_outside_normal_range``, but the text says what the absence means for
  that specific field — sometimes good news (no debt to service), sometimes a
  pointer to a sibling metric that stays defined (negative earnings ->
  ``earnings_yield``), sometimes just unreported data.
- ``falls_outside_normal_range`` is literal: ``True`` whenever the value sits
  outside the reference bands in either direction, unusually strong included
  (a net cash position flags just like distress-level leverage). The
  interpretation text carries the direction.
- Band boundaries are contiguous half-open intervals resolved by an if/elif
  ladder in ascending value order; the ladder is the band table.
- Interpreters are single-value by design. Cross-metric reads — the quick
  ratio against the current ratio, price to book against return on equity,
  dividend yield with the payout ratio — are the interpretation agent's job;
  the strings name the sibling field to cross-check instead of taking it as
  an input.
"""

from dataclasses import dataclass

from stock_analyst.analysis import calculations


@dataclass(frozen=True)
class CalculationInterpretation:
    """One ``CalculatedValues`` field read into plain language: the raw
    value, what it means at this specific level, and whether it sits outside
    the practitioner reference bands in ``docs/fundamental_metrics.md``.
    """

    # The value exactly as it appears on CalculatedValues — a float for the
    # numeric metrics, a zone label string for the Altman zone fields, or None
    # when the metric was not computable.
    raw_value: float | str | None

    # The CalculatedValues field name this interprets.
    field_name: str

    # Plain-language reading of this specific value: which reference band it
    # falls in, what that implies, and the sector caveats or sibling metrics
    # to cross-check. When raw_value is None, this explains what the absence
    # means for this field — sometimes good news (no debt), sometimes a signal
    # to fall back to a sibling metric, sometimes just unreported data.
    interpretation: str

    # True when the value falls outside the reference bands in either
    # direction — unusually strong counts as much as unusually weak (a net
    # cash position is flagged even though it is a strength). Read the
    # interpretation for the direction; this flag only means 'look closer',
    # not 'bad'. Always False when raw_value is None.
    falls_outside_normal_range: bool


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _as_percentage(value: float) -> str:
    """Render a decimal fraction for prose: 0.234 -> '23.4%'."""
    return f"{value:.1%}"


def _as_multiple(value: float) -> str:
    """Render a ratio, multiple, or score for prose: 17.3 -> '17.30'."""
    return f"{value:.2f}"


def _as_currency_amount(value: float) -> str:
    """Render an absolute amount in the filing's currency: 1234567.0 -> '1,234,567'."""
    return f"{value:,.0f}"


# ---------------------------------------------------------------------------
# Building blocks shared across pillars
# ---------------------------------------------------------------------------


def interpret_gross_profit(value: float | None) -> CalculationInterpretation:
    """Interpret revenue minus cost of goods sold."""
    if value is None:
        interpretation = (
            "Not computed — revenue or cost of goods sold was not reported."
            " Expected for banks and insurers, whose filings have no cost of"
            " goods sold line."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Gross profit of {_as_currency_amount(value)} is negative — the"
            " company sells below direct product cost, a severe flag at any"
            " scale."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Gross profit of {_as_currency_amount(value)} is positive. An"
            " absolute amount in the filing's currency, so not comparable"
            " across companies — judge the level through gross_profit_margin."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="gross_profit",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_earnings_before_interest_taxes_depreciation_and_amortization(
    value: float | None,
) -> CalculationInterpretation:
    """Interpret operating income plus depreciation and amortization (EBITDA)."""
    if value is None:
        interpretation = (
            "Not computed — operating income or depreciation and amortization"
            " was not reported. The concept is rejected outright for banks"
            " and insurers, so absence there is expected."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"EBITDA of {_as_currency_amount(value)} is negative — severe:"
            " the business is not covering even its cash operating costs"
            " before any interest, taxes, or capital spending."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"EBITDA of {_as_currency_amount(value)} is positive. An absolute"
            " amount, so judge the level through the EBITDA margin and the"
            " coverage and leverage ratios built on it."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="earnings_before_interest_taxes_depreciation_and_amortization",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_effective_tax_rate(value: float | None) -> CalculationInterpretation:
    """Interpret income tax expense / pretax income."""
    if value is None:
        interpretation = (
            "Not computed — either tax expense or pretax income was not"
            " reported, or pretax income was not positive, which makes the"
            " rate uninterpretable (a rate off a pretax loss means nothing)."
        )
        falls_outside_normal_range = False
    elif value < 0.05:
        interpretation = (
            f"Effective tax rate of {_as_percentage(value)} is near zero —"
            " unusual for a US filer (roughly 15-30% is normal). Look for"
            " one-off tax items, valuation-allowance releases, or"
            " foreign-rate effects; the low rate is unlikely to persist."
        )
        falls_outside_normal_range = True
    elif value < 0.15:
        interpretation = (
            f"Effective tax rate of {_as_percentage(value)} is below the"
            " roughly 15-30% band normal for US filers — modestly low, often"
            " foreign-rate mix or tax credits rather than anything alarming."
        )
        falls_outside_normal_range = False
    elif value < 0.30:
        interpretation = (
            f"Effective tax rate of {_as_percentage(value)} is in the"
            " 15-30% band normal for US filers."
        )
        falls_outside_normal_range = False
    elif value < 0.40:
        interpretation = (
            f"Effective tax rate of {_as_percentage(value)} is above the"
            " normal 15-30% band — somewhat high, possibly one-off tax items"
            " or non-deductible charges."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Effective tax rate of {_as_percentage(value)} is above 40% —"
            " unusual. Look for one-off tax items, non-deductible charges, or"
            " a small pretax income base amplifying the rate."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="effective_tax_rate",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_net_operating_profit_after_tax(
    value: float | None,
) -> CalculationInterpretation:
    """Interpret operating income times (1 - effective tax rate) (NOPAT)."""
    if value is None:
        interpretation = (
            "Not computed — operating income or the effective tax rate was"
            " unavailable (the latter goes missing whenever pretax income is"
            " not positive)."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Net operating profit after tax of {_as_currency_amount(value)}"
            " is negative — the operations lose money after tax, before any"
            " financing effects. Return on invested capital is"
            " uninterpretable off a negative numerator."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Net operating profit after tax of {_as_currency_amount(value)}"
            " is positive. Its main use is as the numerator of return on"
            " invested capital; the absolute level says little on its own."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="net_operating_profit_after_tax",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_total_debt(value: float | None) -> CalculationInterpretation:
    """Interpret interest-bearing liabilities plus lease obligations."""
    if value is None:
        interpretation = (
            "Not computed — short-term debt, long-term debt, or lease"
            " obligations were not reported, so the debt stack could not be"
            " assembled."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Total debt of {_as_currency_amount(value)} is negative, which"
            " is impossible for a sum of interest-bearing liabilities —"
            " almost certainly a data or parsing error; verify the inputs."
        )
        falls_outside_normal_range = True
    elif value == 0.0:
        interpretation = (
            "Total debt is zero — the company is debt-free. The coverage and"
            " debt ratios are None by design in this case, not missing data."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Total debt of {_as_currency_amount(value)} — all"
            " interest-bearing liabilities plus lease obligations"
            " (deliberately not total liabilities). An absolute amount; judge"
            " the burden through the leverage and coverage ratios."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="total_debt",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_net_debt(value: float | None) -> CalculationInterpretation:
    """Interpret total debt minus cash and marketable securities."""
    if value is None:
        interpretation = (
            "Not computed — total debt or the cash and marketable-securities"
            " balances were not reported."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Net debt of {_as_currency_amount(value)} is negative — a net"
            " cash position: cash and marketable securities exceed total"
            " debt. Unusual in the literal sense but a strength (common in"
            " large technology firms); leverage risk is essentially nil"
            " regardless of gross debt."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Net debt of {_as_currency_amount(value)} — debt exceeds the"
            " cash pile by this amount. An absolute figure; judge the burden"
            " through net debt to EBITDA and the coverage ratios."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="net_debt",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_working_capital(value: float | None) -> CalculationInterpretation:
    """Interpret current assets minus current liabilities."""
    if value is None:
        interpretation = (
            "Not computed — current assets or current liabilities were not"
            " reported. Expected for banks, which file unclassified balance"
            " sheets with no current/non-current split."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Working capital of {_as_currency_amount(value)} is negative —"
            " current liabilities exceed current assets. Normal and healthy"
            " for some retail and subscription models (customers pay before"
            " suppliers are paid); elsewhere it can signal liquidity strain —"
            " read the current_ratio and operating_cash_flow_ratio before"
            " concluding either way."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Working capital of {_as_currency_amount(value)} is positive —"
            " a short-term buffer, in absolute currency so not comparable"
            " across companies. Graham's solvency screen: long-term debt"
            " should not exceed this figure."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="working_capital",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_invested_capital(value: float | None) -> CalculationInterpretation:
    """Interpret interest-bearing debt plus shareholders' equity minus cash."""
    if value is None:
        interpretation = "Not computed — debt, shareholders' equity, or cash was not reported."
        falls_outside_normal_range = False
    elif value <= 0.0:
        interpretation = (
            f"Invested capital of {_as_currency_amount(value)} is zero or"
            " negative — return on invested capital is uninterpretable on"
            " this base. Often the residue of past write-offs or"
            " buyback-driven negative equity; book capital embeds old"
            " accounting choices."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Invested capital of {_as_currency_amount(value)} is positive —"
            " the denominator for return on invested capital. Note that past"
            " write-offs shrink book capital and mechanically inflate that"
            " return."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="invested_capital",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_earnings_per_share(value: float | None) -> CalculationInterpretation:
    """Interpret (net income - preferred dividends) / weighted-average diluted shares."""
    if value is None:
        interpretation = (
            "Not computed — net income or the weighted-average diluted share"
            " count was not reported."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Earnings per share of {_as_multiple(value)} is negative — a"
            " net loss for the period. The per-share level itself is not"
            " comparable across companies (share counts are arbitrary), but"
            " the sign is a flag in its own right."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Earnings per share of {_as_multiple(value)} in currency per"
            " share. The level is not comparable across companies — its uses"
            " are the growth series and the price ratios."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="earnings_per_share",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_enterprise_value(value: float | None) -> CalculationInterpretation:
    """Interpret market capitalization + debt + preferred + minority interest - cash."""
    if value is None:
        interpretation = (
            "Not computed — market capitalization or one of the balance-sheet"
            " components (debt, cash) was unavailable. Enterprise-value"
            " multiples are undefined for banks and insurers in any case."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Enterprise value of {_as_currency_amount(value)} is negative —"
            " cash exceeds market capitalization plus debt. A rare deep-value"
            " situation or a data error; verify the inputs before using any"
            " enterprise-value multiple."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Enterprise value of {_as_currency_amount(value)} — the price of"
            " the whole operating business, debt included and cash netted"
            " out. Below market capitalization would indicate a net cash"
            " position. Judge the level through the enterprise-value"
            " multiples."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="enterprise_value",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_free_cash_flow(value: float | None) -> CalculationInterpretation:
    """Interpret operating cash flow minus capital expenditures."""
    if value is None:
        interpretation = (
            "Not computed — operating cash flow or capital expenditures were"
            " not reported. Undefined for banks; REITs use funds from"
            " operations instead."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Free cash flow of {_as_currency_amount(value)} is negative —"
            " the business consumed cash after capital spending. Either"
            " growth investment or value destruction; only return on"
            " invested capital context distinguishes them, and a single"
            " period is noisy because capital spending is lumpy."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Free cash flow of {_as_currency_amount(value)} is positive —"
            " cash generated after capital spending. Note stock-based"
            " compensation inflates the operating-cash-flow side; judge the"
            " level through free_cash_flow_margin and free_cash_flow_yield."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="free_cash_flow",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


# ---------------------------------------------------------------------------
# Profitability
# ---------------------------------------------------------------------------


def interpret_gross_profit_margin(value: float | None) -> CalculationInterpretation:
    """Interpret gross profit / revenue."""
    if value is None:
        interpretation = (
            "Not computed — gross profit or revenue was unavailable."
            " Expected for banks and insurers, which have no cost of goods"
            " sold line."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Gross profit margin of {_as_percentage(value)} is negative —"
            " the company sells below direct product cost, a severe flag at"
            " any scale."
        )
        falls_outside_normal_range = True
    elif value < 0.20:
        interpretation = (
            f"Gross profit margin of {_as_percentage(value)} is low in"
            " absolute terms, though cross-industry comparison is nearly"
            " meaningless — distribution and grocery-style retail run this"
            " thin structurally. Compare against peers and the company's own"
            " history; an eroding trend is the early warning."
        )
        falls_outside_normal_range = False
    elif value < 0.70:
        interpretation = (
            f"Gross profit margin of {_as_percentage(value)} sits in the"
            " broad middle of industry norms (retail runs ~20-40%, software"
            " ~70-90%). Only the peer and historical comparison is"
            " informative at this level."
        )
        falls_outside_normal_range = False
    elif value <= 0.90:
        interpretation = (
            f"Gross profit margin of {_as_percentage(value)} is in the"
            " ~70-90% band typical of software and other high-intangible"
            " businesses — high, but normal for those models."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Gross profit margin of {_as_percentage(value)} is above 90% —"
            " beyond even the software norm. Verify what the filer"
            " classifies as cost of goods sold before crediting the margin."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="gross_profit_margin",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_operating_margin(value: float | None) -> CalculationInterpretation:
    """Interpret operating income / revenue."""
    if value is None:
        interpretation = (
            "Not computed — operating income or revenue was not reported."
            " Not meaningful for banks in any case, where interest is the"
            " core operating cost."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Operating margin of {_as_percentage(value)} is negative — the"
            " operations themselves lose money before any financing or tax"
            " effects."
        )
        falls_outside_normal_range = True
    elif value < 0.05:
        interpretation = (
            f"Operating margin of {_as_percentage(value)} is thin (below 5%)"
            " — little cushion against cost inflation or a revenue dip,"
            " though some high-volume industries run here structurally."
        )
        falls_outside_normal_range = False
    elif value < 0.10:
        interpretation = (
            f"Operating margin of {_as_percentage(value)} is modest — below"
            " the roughly 10-20% band considered healthy for most"
            " industries."
        )
        falls_outside_normal_range = False
    elif value < 0.20:
        interpretation = (
            f"Operating margin of {_as_percentage(value)} is healthy —"
            " within the roughly 10-20% band, around the large-cap US"
            " median (low-to-mid teens percent)."
        )
        falls_outside_normal_range = False
    elif value < 0.40:
        interpretation = (
            f"Operating margin of {_as_percentage(value)} is strong — above"
            " 20%, well clear of the large-cap US median."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Operating margin of {_as_percentage(value)} is above 40% —"
            " unusual. Verify what the filer classifies as operating costs"
            " before crediting the margin."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="operating_margin",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_net_profit_margin(value: float | None) -> CalculationInterpretation:
    """Interpret net income / revenue."""
    if value is None:
        interpretation = "Not computed — net income or revenue was not reported."
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Net profit margin of {_as_percentage(value)} is negative — a net loss for the period."
        )
        falls_outside_normal_range = True
    elif value < 0.05:
        interpretation = (
            f"Net profit margin of {_as_percentage(value)} is thin (below"
            " 5%) — profitability is fragile against cost or revenue shocks."
        )
        falls_outside_normal_range = False
    elif value < 0.10:
        interpretation = f"Net profit margin of {_as_percentage(value)} is about average (5-10%)."
        falls_outside_normal_range = False
    elif value < 0.20:
        interpretation = f"Net profit margin of {_as_percentage(value)} is good (10-20%)."
        falls_outside_normal_range = False
    elif value < 0.30:
        interpretation = (
            f"Net profit margin of {_as_percentage(value)} is excellent"
            " (20-30%). Note REITs run structurally depressed here because"
            " of property depreciation, so a REIT at a lower level is not"
            " comparable."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Net profit margin of {_as_percentage(value)} is above 30% —"
            " unusual. Check for one-off gains or tax items before crediting"
            " the underlying business."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="net_profit_margin",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_earnings_before_interest_taxes_depreciation_and_amortization_margin(
    value: float | None,
) -> CalculationInterpretation:
    """Interpret EBITDA / revenue."""
    if value is None:
        interpretation = (
            "Not computed — EBITDA or revenue was unavailable. Not"
            " meaningful for financials in any case."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"EBITDA margin of {_as_percentage(value)} is negative — severe:"
            " revenue does not cover even cash operating costs."
        )
        falls_outside_normal_range = True
    elif value < 0.10:
        interpretation = (
            f"EBITDA margin of {_as_percentage(value)} is thin (below 10%),"
            " though normal in distribution and retail. Remember this is a"
            " comps convenience, not a quality signal — depreciation is a"
            " real cost."
        )
        falls_outside_normal_range = False
    elif value < 0.30:
        interpretation = (
            f"EBITDA margin of {_as_percentage(value)} covers the typical"
            " industrial range (~15-25%). Depreciation is a real cost, so"
            " cross-check the operating margin before crediting the level."
        )
        falls_outside_normal_range = False
    elif value < 0.60:
        interpretation = (
            f"EBITDA margin of {_as_percentage(value)} is high — the"
            " 30-40%-plus territory of software, pharma, and infrastructure"
            " models. Normal for those sectors, notable elsewhere."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"EBITDA margin of {_as_percentage(value)} is above 60% — beyond"
            " even the software/pharma/infrastructure norm; verify the"
            " revenue and cost classification."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="earnings_before_interest_taxes_depreciation_and_amortization_margin",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


# ---------------------------------------------------------------------------
# Liquidity
# ---------------------------------------------------------------------------


def interpret_current_ratio(value: float | None) -> CalculationInterpretation:
    """Interpret current assets / current liabilities."""
    if value is None:
        interpretation = (
            "Not computed — current assets or current liabilities were not"
            " reported. Expected for banks and insurers, which file"
            " unclassified balance sheets."
        )
        falls_outside_normal_range = False
    elif value < 1.0:
        interpretation = (
            f"Current ratio of {_as_multiple(value)} is below 1 — short-term"
            " obligations exceed short-term assets. Normal and healthy for"
            " some retail and subscription models (customers pay before"
            " suppliers are paid); elsewhere a liquidity concern —"
            " cross-check the flow-based operating_cash_flow_ratio."
        )
        falls_outside_normal_range = True
    elif value < 2.0:
        interpretation = (
            f"Current ratio of {_as_multiple(value)} — short-term assets"
            " cover short-term obligations, though below Graham's defensive"
            " standard of 2.0 for industrials. Note the ratio is inflated by"
            " slow-moving inventory and stale receivables; the quick_ratio"
            " spread shows how much."
        )
        falls_outside_normal_range = False
    elif value < 3.0:
        interpretation = (
            f"Current ratio of {_as_multiple(value)} meets Graham's"
            " defensive standard of 2.0+ for industrials — a comfortable"
            " short-term cushion."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Current ratio of {_as_multiple(value)} is very high — the"
            " cushion is beyond any defensive need and can signal lazy"
            " capital sitting in low-return current assets."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="current_ratio",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_quick_ratio(value: float | None) -> CalculationInterpretation:
    """Interpret (cash + short-term investments + receivables) / current liabilities."""
    if value is None:
        interpretation = (
            "Not computed — an input (cash, receivables, or current"
            " liabilities) was not reported. Expected for banks."
        )
        falls_outside_normal_range = False
    elif value < 1.0:
        interpretation = (
            f"Quick ratio of {_as_multiple(value)} is below the ~1 level"
            " typically considered healthy — without selling inventory, the"
            " liquid assets don't cover current liabilities. The real signal"
            " is the spread versus the current_ratio: a big gap flags an"
            " inventory-heavy or inventory-stuck balance sheet."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Quick ratio of {_as_multiple(value)} is at or above the ~1"
            " level typically considered healthy — liquid assets alone cover"
            " current liabilities. Compare against the current_ratio: a"
            " small spread means little inventory (the two are redundant for"
            " no-inventory businesses)."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="quick_ratio",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_cash_ratio(value: float | None) -> CalculationInterpretation:
    """Interpret (cash + short-term investments) / current liabilities."""
    if value is None:
        interpretation = (
            "Not computed — cash balances or current liabilities were not"
            " reported. Expected for banks."
        )
        falls_outside_normal_range = False
    elif value < 0.1:
        interpretation = (
            f"Cash ratio of {_as_multiple(value)} is below the 0.1-0.5 range"
            " healthy firms typically run — in a worst-case crunch, cash"
            " alone covers little of the current liabilities. Read with the"
            " broader liquidity ratios before concluding distress."
        )
        falls_outside_normal_range = True
    elif value < 0.5:
        interpretation = (
            f"Cash ratio of {_as_multiple(value)} is in the 0.1-0.5 range"
            " healthy firms typically run — this is the worst-case crisis"
            " measure, so a fractional level is normal."
        )
        falls_outside_normal_range = False
    elif value < 1.0:
        interpretation = (
            f"Cash ratio of {_as_multiple(value)} is above the typical"
            " 0.1-0.5 range — an ample cash position relative to short-term"
            " obligations."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Cash ratio of {_as_multiple(value)} is above 1 — current"
            " liabilities are fully covered by cash alone. Either an"
            " idle-cash hoard or a deliberate war chest; read with the"
            " capital-return metrics (dividend_yield, shareholder_yield)."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="cash_ratio",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_operating_cash_flow_ratio(value: float | None) -> CalculationInterpretation:
    """Interpret operating cash flow / current liabilities."""
    if value is None:
        interpretation = (
            "Not computed — operating cash flow or current liabilities were"
            " not reported. Not meaningful for banks, where loan and deposit"
            " flows distort it."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Operating cash flow ratio of {_as_multiple(value)} is negative"
            " — operations consumed cash over the period while short-term"
            " obligations wait. A serious liquidity flag unless clearly a"
            " one-period working-capital swing."
        )
        falls_outside_normal_range = True
    elif value < 1.0:
        interpretation = (
            f"Operating cash flow ratio of {_as_multiple(value)} is below 1"
            " — operations alone do not cover current liabilities within the"
            " period. Common even at healthy firms (this is a strict test);"
            " it matters most when the balance-sheet ratios are also weak."
            " This is the strongest liquidity cross-check because it is"
            " flow-based and hard to window-dress."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Operating cash flow ratio of {_as_multiple(value)} is above 1"
            " — operations alone cover short-term obligations. The strongest"
            " form of liquidity, being flow-based and hard to window-dress."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="operating_cash_flow_ratio",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_defensive_interval_ratio(value: float | None) -> CalculationInterpretation:
    """Interpret days the firm can operate on liquid assets with zero revenue."""
    if value is None:
        interpretation = (
            "Not computed — liquid-asset balances or daily operating expenses were unavailable."
        )
        falls_outside_normal_range = False
    elif value < 30.0:
        interpretation = (
            f"Defensive interval of {_as_multiple(value)} days is tight"
            " (below 30) — with zero revenue the firm depends on near-term"
            " collections or financing to keep operating."
        )
        falls_outside_normal_range = True
    elif value < 90.0:
        interpretation = (
            f"Defensive interval of {_as_multiple(value)} days is adequate"
            " (30-90) — liquid assets fund one to three months of operations"
            " with zero revenue."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Defensive interval of {_as_multiple(value)} days is"
            " comfortable (above 90) — liquid assets fund a quarter or more"
            " of operations even with zero revenue."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="defensive_interval_ratio",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


# ---------------------------------------------------------------------------
# Solvency & leverage
# ---------------------------------------------------------------------------


def interpret_debt_to_equity(value: float | None) -> CalculationInterpretation:
    """Interpret total debt / shareholders' equity."""
    if value is None:
        interpretation = (
            "Not computed — either an input was not reported, or"
            " shareholders' equity is not positive (common in buyback-heavy"
            " large-caps). If the latter, that is itself notable — fall back"
            " to debt_to_capital, which stays bounded."
        )
        falls_outside_normal_range = False
    elif value < 1.0:
        interpretation = (
            f"Debt to equity of {_as_multiple(value)} is below 1.0 — within"
            " the common conservative screen for industrials: equity"
            " finances more of the business than debt does."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Debt to equity of {_as_multiple(value)} is above the 1.0"
            " conservative screen for industrials. Sector norms dominate,"
            " though — utilities and REITs run high by design, and"
            " financials are structurally high because debt is their raw"
            " material — so read against peers before concluding"
            " overleverage."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="debt_to_equity",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_debt_to_assets(value: float | None) -> CalculationInterpretation:
    """Interpret total debt / total assets."""
    if value is None:
        interpretation = "Not computed — total debt or total assets was not reported."
        falls_outside_normal_range = False
    elif value <= 0.5:
        interpretation = (
            f"Debt to assets of {_as_multiple(value)} — the asset base is"
            " majority equity- and liability-funded rather than debt-funded."
            " Bounded 0-1, so it stays well-behaved even when equity is thin"
            " or negative."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Debt to assets of {_as_multiple(value)} is above 0.5 — the"
            " asset base is majority debt-funded. Read with the coverage"
            " ratios to judge whether the load is serviceable."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="debt_to_assets",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_debt_to_capital(value: float | None) -> CalculationInterpretation:
    """Interpret total debt / (total debt + equity)."""
    if value is None:
        interpretation = "Not computed — total debt or shareholders' equity was not reported."
        falls_outside_normal_range = False
    elif value < 0.4:
        interpretation = (
            f"Debt to capital of {_as_multiple(value)} is conservative"
            " (below the 0.3-0.4 threshold for non-financials) — debt is a"
            " minority of the capital structure."
        )
        falls_outside_normal_range = False
    elif value < 0.6:
        interpretation = (
            f"Debt to capital of {_as_multiple(value)} is moderate (0.4-0.6"
            " for non-financials) — a balanced capital structure by the"
            " credit-analyst convention."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Debt to capital of {_as_multiple(value)} is aggressive (above"
            " 0.6 for non-financials) — debt dominates the capital"
            " structure; read with the coverage ratios."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="debt_to_capital",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization(
    value: float | None,
) -> CalculationInterpretation:
    """Interpret net debt / EBITDA — years of EBITDA needed to repay net debt."""
    if value is None:
        interpretation = (
            "Not computed — either an input was not reported, or EBITDA was"
            " not positive, which makes years-to-repay uninterpretable. If"
            " earnings were the problem, judge the debt load from the"
            " balance sheet instead (debt_to_capital, debt_to_assets)."
            " Meaningless for banks in any case."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Net debt to EBITDA of {_as_multiple(value)} is negative —"
            " a net cash position: cash exceeds total debt. Unusual in the"
            " literal sense, but a strength; leverage risk is essentially"
            " nil regardless of gross debt."
        )
        falls_outside_normal_range = True
    elif value < 1.5:
        interpretation = (
            f"Net debt to EBITDA of {_as_multiple(value)} is minimal"
            " leverage by credit-practice tiers — under a year and a half of"
            " EBITDA would clear the net debt."
        )
        falls_outside_normal_range = False
    elif value < 3.0:
        interpretation = (
            f"Net debt to EBITDA of {_as_multiple(value)} is intermediate"
            " leverage — normal for a stable business, but check that EBITDA"
            " is not at a cyclical peak, which flatters the ratio."
        )
        falls_outside_normal_range = False
    elif value < 4.0:
        interpretation = (
            f"Net debt to EBITDA of {_as_multiple(value)} is significant"
            " leverage — this 3-4 range is a common bank covenant ceiling."
            " Note REITs structurally run 5-7 on their industry variant, so"
            " read sector context first."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Net debt to EBITDA of {_as_multiple(value)} is highly"
            " leveraged by credit-practice tiers (above 4-5) — debt"
            " repayment dominates the equity story unless this is a REIT or"
            " utility, where high leverage is the business model."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name=("net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization"),
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_interest_coverage(value: float | None) -> CalculationInterpretation:
    """Interpret operating income / gross interest expense."""
    if value is None:
        interpretation = (
            "Not computed. When interest expense is zero this is good news"
            " rather than missing data — the company has no debt to service."
            " Otherwise operating income or interest expense was simply not"
            " reported. Not meaningful for banks either way (interest is"
            " their core operating cost)."
        )
        falls_outside_normal_range = False
    elif value < 1.5:
        interpretation = (
            f"Interest coverage of {_as_multiple(value)} is distress"
            " territory (below 1.5-2) — operating income barely covers, or"
            " fails to cover, the interest bill; refinancing risk dominates."
        )
        falls_outside_normal_range = True
    elif value < 3.0:
        interpretation = (
            f"Interest coverage of {_as_multiple(value)} is thin — below"
            " the roughly 3-4.25 band Damodaran maps to an A- synthetic"
            " rating; little room for an earnings dip."
        )
        falls_outside_normal_range = True
    elif value < 5.0:
        interpretation = (
            f"Interest coverage of {_as_multiple(value)} is adequate — in"
            " the investment-grade span of Damodaran's synthetic-rating map"
            " for large non-financials."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Interest coverage of {_as_multiple(value)} is comfortable —"
            " above 5, and 8.5+ maps to a AAA synthetic rating; debt service"
            " is not a constraint."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="interest_coverage",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage(
    value: float | None,
) -> CalculationInterpretation:
    """Interpret EBITDA / interest expense."""
    if value is None:
        interpretation = (
            "Not computed. When interest expense is zero this is good news"
            " rather than missing data — no debt to service. Otherwise"
            " EBITDA or interest expense was not reported."
        )
        falls_outside_normal_range = False
    elif value < 2.0:
        interpretation = (
            f"EBITDA interest coverage of {_as_multiple(value)} is stressed"
            " (below 2) — and this is the generous variant that adds back"
            " depreciation, so the strain is worse than it looks."
        )
        falls_outside_normal_range = True
    elif value < 6.0:
        interpretation = (
            f"EBITDA interest coverage of {_as_multiple(value)} is"
            " intermediate (2-6 in credit practice). Remember this variant"
            " runs above the operating-income form by construction —"
            " cross-check interest_coverage."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"EBITDA interest coverage of {_as_multiple(value)} is"
            " comfortable (above 6 in credit practice) — cash operating"
            " earnings cover the interest bill many times over."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name=(
            "earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage"
        ),
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_operating_cash_flow_to_debt(value: float | None) -> CalculationInterpretation:
    """Interpret operating cash flow / total debt."""
    if value is None:
        interpretation = (
            "Not computed. When total debt is zero this is good news rather"
            " than missing data — the company is debt-free. Otherwise"
            " operating cash flow or total debt was not reported."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Operating cash flow to debt of {_as_multiple(value)} is"
            " negative — operations consumed cash while the debt stack"
            " stands; the debt cannot be serviced internally at this rate."
        )
        falls_outside_normal_range = True
    elif value < 0.40:
        interpretation = (
            f"Operating cash flow to debt of {_as_multiple(value)} is below"
            " the ~0.40 level associated with strong investment-grade credit"
            " — internally generated cash retires the debt stack slowly;"
            " read with the coverage ratios."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Operating cash flow to debt of {_as_multiple(value)} is at or"
            " above the ~0.40 level associated with strong investment-grade"
            " credit — internally generated cash could retire the whole debt"
            " stack in a few years."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="operating_cash_flow_to_debt",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


# ---------------------------------------------------------------------------
# Cash flow - generation & quality
# ---------------------------------------------------------------------------


def interpret_free_cash_flow_margin(value: float | None) -> CalculationInterpretation:
    """Interpret free cash flow / revenue."""
    if value is None:
        interpretation = "Not computed — free cash flow or revenue was unavailable."
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Free cash flow margin of {_as_percentage(value)} is negative —"
            " the business consumed cash after capital spending. Smooth over"
            " multiple years before judging: capital spending is lumpy."
        )
        falls_outside_normal_range = True
    elif value < 0.10:
        interpretation = (
            f"Free cash flow margin of {_as_percentage(value)} is in the"
            " single digits — normal in retail and other thin-margin"
            " sectors; below the ~10% level generally considered strong."
        )
        falls_outside_normal_range = False
    elif value < 0.20:
        interpretation = (
            f"Free cash flow margin of {_as_percentage(value)} is strong"
            " (above 10%; manufacturing typically runs 10-15%)."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Free cash flow margin of {_as_percentage(value)} is in"
            " software-leader territory (above 20%) — exceptional cash-based"
            " profitability."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="free_cash_flow_margin",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_operating_cash_flow_to_net_income(
    value: float | None,
) -> CalculationInterpretation:
    """Interpret operating cash flow / net income — the earnings-quality check."""
    if value is None:
        interpretation = (
            "Not computed — net income was not positive (the ratio explodes"
            " near zero) or an input was missing. Use the sloan_accruals_ratio"
            " instead; it stays defined."
        )
        falls_outside_normal_range = False
    elif value < 1.0:
        interpretation = (
            f"Operating cash flow to net income of {_as_multiple(value)} is"
            " below 1 — reported earnings ran ahead of cash, i.e."
            " accrual-driven. Depreciation alone should push most firms"
            " above 1, so this warrants a look — though one year can be"
            " working-capital timing noise; it is persistence that convicts."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Operating cash flow to net income of {_as_multiple(value)} is"
            " at or above 1 — earnings are backed by cash, the healthy"
            " pattern (depreciation alone should push most firms above 1)."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="operating_cash_flow_to_net_income",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_sloan_accruals_ratio(value: float | None) -> CalculationInterpretation:
    """Interpret (net income - operating cash flow - investing cash flow) / total assets."""
    if value is None:
        interpretation = (
            "Not computed — net income, a cash-flow statement value, or"
            " total assets was not reported."
        )
        falls_outside_normal_range = False
    elif value < -0.10:
        interpretation = (
            f"Sloan accruals ratio of {_as_multiple(value)} is below the"
            " -0.10 to +0.10 safe band on the negative side — cash flows ran"
            " well ahead of reported income, often heavy write-downs or"
            " impairments depressing earnings. Not the classic accrual"
            " warning, but check what drove the gap."
        )
        falls_outside_normal_range = True
    elif value <= 0.10:
        interpretation = (
            f"Sloan accruals ratio of {_as_multiple(value)} is inside the"
            " -0.10 to +0.10 safe band — no accrual-quality warning."
        )
        falls_outside_normal_range = False
    elif value < 0.25:
        interpretation = (
            f"Sloan accruals ratio of {_as_multiple(value)} is above the"
            " +0.10 safe ceiling — earnings are running ahead of cash by an"
            " elevated margin; earnings quality deserves scrutiny."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Sloan accruals ratio of {_as_multiple(value)} is above +0.25 —"
            " a strong warning: high-accrual firms systematically"
            " underperform (Sloan 1996)."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="sloan_accruals_ratio",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_free_cash_flow_conversion(value: float | None) -> CalculationInterpretation:
    """Interpret free cash flow / EBITDA."""
    if value is None:
        interpretation = (
            "Not computed — EBITDA was not positive (conversion of a"
            " negative base means nothing) or an input was missing. Judge"
            " cash generation directly from free_cash_flow_margin instead."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Free cash flow conversion of {_as_multiple(value)} is negative"
            " — positive EBITDA turned into negative free cash flow, eaten"
            " by capital spending, working capital, interest, or taxes."
            " Check capital_expenditure_intensity for the likely culprit."
        )
        falls_outside_normal_range = True
    elif value < 0.8:
        interpretation = (
            f"Free cash flow conversion of {_as_multiple(value)} is below"
            " the 0.8 level considered strong — a meaningful share of EBITDA"
            " never becomes free cash. Normal for capital-intensive"
            " businesses; check capital_expenditure_intensity."
        )
        falls_outside_normal_range = False
    elif value <= 1.0:
        interpretation = (
            f"Free cash flow conversion of {_as_multiple(value)} is strong"
            " (0.8 is strong, ~1.0 ideal) — EBITDA translates almost fully"
            " into free cash."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Free cash flow conversion of {_as_multiple(value)} is above 1"
            " — usually a temporary working-capital benefit rather than a"
            " durable feature; do not extrapolate it."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="free_cash_flow_conversion",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_capital_expenditure_intensity(
    value: float | None,
) -> CalculationInterpretation:
    """Interpret capital expenditures / revenue."""
    if value is None:
        interpretation = "Not computed — capital expenditures or revenue was not reported."
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Capital expenditure intensity of {_as_percentage(value)} is"
            " negative, which is impossible under this codebase's"
            " positive-magnitude convention for capital expenditures —"
            " almost certainly a parsing or sign error; verify the inputs."
        )
        falls_outside_normal_range = True
    elif value < 0.05:
        interpretation = (
            f"Capital expenditure intensity of {_as_percentage(value)} is"
            " asset-light (below 5% of revenue)."
        )
        falls_outside_normal_range = False
    elif value < 0.15:
        interpretation = (
            f"Capital expenditure intensity of {_as_percentage(value)} is"
            " moderate (5-15% of revenue). Capital spending is lumpy —"
            " average over 3-5 years before drawing conclusions."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Capital expenditure intensity of {_as_percentage(value)} is"
            " capital-intensive (above 15% of revenue). Not bad in itself —"
            " high spending only destroys value when the returns on it are"
            " poor — and spending is lumpy, so average over 3-5 years."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="capital_expenditure_intensity",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_capital_expenditures_to_depreciation(
    value: float | None,
) -> CalculationInterpretation:
    """Interpret capital expenditures / depreciation and amortization."""
    if value is None:
        interpretation = (
            "Not computed — capital expenditures or depreciation and amortization was not reported."
        )
        falls_outside_normal_range = False
    elif value < 1.0:
        interpretation = (
            f"Capital expenditures to depreciation of {_as_multiple(value)}"
            " is below 1 — spending less than the assets are wearing down, a"
            " rough proxy for underinvestment and, if sustained, an aging"
            " asset base. Capital spending is lumpy, so confirm across"
            " several periods before concluding."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Capital expenditures to depreciation of {_as_multiple(value)}"
            " is at or above 1 — the asset base is being maintained or"
            " grown."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="capital_expenditures_to_depreciation",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


# ---------------------------------------------------------------------------
# Growth
# ---------------------------------------------------------------------------


def interpret_retention_rate(value: float | None) -> CalculationInterpretation:
    """Interpret 1 - payout ratio: the share of earnings reinvested."""
    if value is None:
        interpretation = (
            "Not computed — the payout ratio was unavailable (net income not"
            " positive, or dividends not reported — an absent dividend line"
            " is not provably a zero flow)."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Retention rate of {_as_percentage(value)} is negative — the"
            " company paid out more in dividends than it earned (payout"
            " ratio above 1), an unsustainable arrangement funded from the"
            " balance sheet or borrowings."
        )
        falls_outside_normal_range = True
    elif value < 0.4:
        interpretation = (
            f"Retention rate of {_as_percentage(value)} — most earnings are"
            " paid out rather than reinvested, the profile of a mature"
            " dividend payer. Read with payout_ratio and dividend_yield."
        )
        falls_outside_normal_range = False
    elif value < 0.8:
        interpretation = (
            f"Retention rate of {_as_percentage(value)} — a balanced split"
            " between reinvestment and payout."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Retention rate of {_as_percentage(value)} — nearly all"
            " earnings are reinvested, typical for growth firms paying"
            " little or no dividend."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="retention_rate",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------


def interpret_price_to_earnings(value: float | None) -> CalculationInterpretation:
    """Interpret market capitalization / trailing net income."""
    if value is None:
        interpretation = (
            "Not computed — earnings were not positive (the multiple is"
            " undefined on a loss) or market capitalization was unavailable."
            " Rank on earnings_yield instead; it stays defined for negative"
            " earnings."
        )
        falls_outside_normal_range = False
    elif value < 10.0:
        interpretation = (
            f"Price to earnings of {_as_multiple(value)} is below 10 —"
            " priced for decline or deep value. Verify earnings are not at a"
            " cyclical peak: for cyclicals the ratio is lowest exactly at"
            " the earnings peak. Misleading for REITs (use price to funds"
            " from operations)."
        )
        falls_outside_normal_range = True
    elif value < 15.0:
        interpretation = (
            f"Price to earnings of {_as_multiple(value)} is modestly below"
            " the long-run US market average of roughly 15-20."
        )
        falls_outside_normal_range = False
    elif value < 20.0:
        interpretation = (
            f"Price to earnings of {_as_multiple(value)} is in line with the"
            " long-run US market average of roughly 15-20."
        )
        falls_outside_normal_range = False
    elif value < 30.0:
        interpretation = (
            f"Price to earnings of {_as_multiple(value)} carries a growth"
            " premium (20-30) — the price assumes meaningful earnings"
            " growth."
        )
        falls_outside_normal_range = False
    elif value < 50.0:
        interpretation = (
            f"Price to earnings of {_as_multiple(value)} is rich — above the"
            " 20-30 growth-premium band. Either aggressive growth pricing or"
            " temporarily depressed earnings inflating the multiple; inspect"
            " the earnings before calling it expensive."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Price to earnings of {_as_multiple(value)} is above 50 —"
            " speculative growth pricing or a trough-earnings artifact."
            " Inspect the earnings, don't just call it expensive."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="price_to_earnings",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_earnings_yield(value: float | None) -> CalculationInterpretation:
    """Interpret net income / market capitalization."""
    if value is None:
        interpretation = (
            "Not computed — net income or market capitalization was"
            " unavailable (unlike price to earnings, this stays defined for"
            " negative earnings, so absence means missing data)."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Earnings yield of {_as_percentage(value)} is negative — the"
            " company is loss-making at the current price. This form exists"
            " precisely to rank such companies, which price to earnings"
            " cannot."
        )
        falls_outside_normal_range = True
    elif value < 0.02:
        interpretation = (
            f"Earnings yield of {_as_percentage(value)} is very low — well"
            " below any recent 10-year Treasury yield, so the price is"
            " justified only by substantial expected growth."
        )
        falls_outside_normal_range = True
    elif value < 0.08:
        interpretation = (
            f"Earnings yield of {_as_percentage(value)} is unremarkable."
            " Compare against the prevailing 10-year Treasury yield: a yield"
            " below the risk-free rate means the price leans on expected"
            " growth."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Earnings yield of {_as_percentage(value)} is high (above 8%) —"
            " cheap relative to earnings, or the market doubts those"
            " earnings persist. Cross-check free_cash_flow_yield: a wide gap"
            " between the two is an accrual-quality flag."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="earnings_yield",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_earnings_before_interest_and_taxes_to_enterprise_value(
    value: float | None,
) -> CalculationInterpretation:
    """Interpret operating income / enterprise value (Greenblatt earnings yield)."""
    if value is None:
        interpretation = (
            "Not computed — operating income or enterprise value was"
            " unavailable. Inapplicable to financials in any case."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Operating income to enterprise value of {_as_percentage(value)}"
            " is negative — the operations lose money (or enterprise value"
            " is negative; verify which)."
        )
        falls_outside_normal_range = True
    elif value < 0.10:
        interpretation = (
            f"Operating income to enterprise value of {_as_percentage(value)}"
            " is below the ~10% level Greenblatt treats as classic cheap"
            " territory — a normal-to-expensive capital-structure-neutral"
            " earnings yield."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Operating income to enterprise value of {_as_percentage(value)}"
            " is above ~10% — classic cheap territory by Greenblatt's"
            " screen. Verify operating income is not at a cyclical peak."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="earnings_before_interest_and_taxes_to_enterprise_value",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_price_to_book(value: float | None) -> CalculationInterpretation:
    """Interpret market capitalization / common book equity."""
    if value is None:
        interpretation = (
            "Not computed — book equity was not positive (itself notable:"
            " buybacks or accumulated losses have consumed the equity"
            " account) or market capitalization was unavailable. Lean on the"
            " earnings- and cash-flow-based multiples instead."
        )
        falls_outside_normal_range = False
    elif value < 1.0:
        interpretation = (
            f"Price to book of {_as_multiple(value)} is below 1 — the"
            " company trades below its accounting net asset value. Either"
            " cheap or the business is in trouble; the justified level rises"
            " with return on equity, so always read the pair. This is the"
            " most meaningful multiple for banks and insurers."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Price to book of {_as_multiple(value)} — the market values the"
            " company above accounting net worth, as it should for any"
            " decent return on equity. Historical-cost accounting and"
            " expensed intangibles understate true equity for asset-light"
            " firms, so a high multiple says little about software"
            " companies; most meaningful for banks and insurers."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="price_to_book",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_price_to_sales(value: float | None) -> CalculationInterpretation:
    """Interpret market capitalization / trailing revenue."""
    if value is None:
        interpretation = (
            "Not computed — revenue or market capitalization was"
            " unavailable. Not applicable to financials in any case."
        )
        falls_outside_normal_range = False
    elif value < 1.0:
        interpretation = (
            f"Price to sales of {_as_multiple(value)} is below 1 — cheap per"
            " revenue dollar, or a structurally low-margin business. Must be"
            " read with net_profit_margin: a high-margin and a zero-margin"
            " firm at the same multiple are not equally valued."
        )
        falls_outside_normal_range = True
    elif value < 2.0:
        interpretation = (
            f"Price to sales of {_as_multiple(value)} is typical for a"
            " mature company (~1-2). Read jointly with net_profit_margin."
        )
        falls_outside_normal_range = False
    elif value < 10.0:
        interpretation = (
            f"Price to sales of {_as_multiple(value)} carries a growth or"
            " margin premium (above the ~1-2 mature-company range). Only"
            " high margins or strong growth justify it — check"
            " net_profit_margin."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Price to sales of {_as_multiple(value)} is above 10 — a level"
            " that demands exceptional growth plus high margins to ever pay"
            " off."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="price_to_sales",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization(
    value: float | None,
) -> CalculationInterpretation:
    """Interpret enterprise value / EBITDA."""
    if value is None:
        interpretation = (
            "Not computed — EBITDA was not positive (the multiple is"
            " undefined on a loss) or enterprise value was unavailable."
            " Fall back to enterprise_value_to_sales. Never applicable to"
            " financials."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Enterprise value to EBITDA of {_as_multiple(value)} is"
            " negative — enterprise value is below zero (cash exceeds market"
            " capitalization plus debt): a rare deep-value situation or a"
            " data error; verify the inputs."
        )
        falls_outside_normal_range = True
    elif value < 6.0:
        interpretation = (
            f"Enterprise value to EBITDA of {_as_multiple(value)} is cheap"
            " (below 6) — or the market is pricing decline. The broad market"
            " typically trades ~8-12."
        )
        falls_outside_normal_range = True
    elif value < 12.0:
        interpretation = (
            f"Enterprise value to EBITDA of {_as_multiple(value)} is in or"
            " near the broad-market range (~8-12). The multiple ignores"
            " capital spending, so it flatters capital-intensive firms —"
            " cross-check enterprise_value_to_earnings_before_interest_and_taxes."
        )
        falls_outside_normal_range = False
    elif value < 15.0:
        interpretation = (
            f"Enterprise value to EBITDA of {_as_multiple(value)} is above"
            " the broad-market ~8-12 range — a premium that needs growth or"
            " quality to justify."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Enterprise value to EBITDA of {_as_multiple(value)} is rich"
            " (above 15) — growth-priced for a mature firm; the multiple"
            " also ignores capital spending, so cross-check the"
            " operating-income form."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name=(
            "enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization"
        ),
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_enterprise_value_to_earnings_before_interest_and_taxes(
    value: float | None,
) -> CalculationInterpretation:
    """Interpret enterprise value / operating income."""
    if value is None:
        interpretation = (
            "Not computed — operating income was not positive or enterprise"
            " value was unavailable. Fall back to enterprise_value_to_sales."
            " Not applicable to financials."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Enterprise value to operating income of {_as_multiple(value)}"
            " is negative — enterprise value is below zero: a rare"
            " deep-value situation or a data error; verify the inputs."
        )
        falls_outside_normal_range = True
    elif value < 10.0:
        interpretation = (
            f"Enterprise value to operating income of {_as_multiple(value)}"
            " is below 10 — classic Greenblatt-cheap territory (its inverse"
            " is above the ~10% earnings-yield screen). Verify operating"
            " income is not at a cyclical peak."
        )
        falls_outside_normal_range = True
    elif value < 14.0:
        interpretation = (
            f"Enterprise value to operating income of {_as_multiple(value)}"
            " is typical (~10-14). This form charges for depreciation, so"
            " prefer it over the EBITDA form when comparing firms of"
            " different capital intensity."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Enterprise value to operating income of {_as_multiple(value)}"
            " is above the typical ~10-14 range — a premium that needs"
            " growth or quality to justify."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="enterprise_value_to_earnings_before_interest_and_taxes",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_enterprise_value_to_sales(value: float | None) -> CalculationInterpretation:
    """Interpret enterprise value / trailing revenue."""
    if value is None:
        interpretation = (
            "Not computed — revenue or enterprise value was unavailable."
            " Not applicable to financials in any case."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Enterprise value to sales of {_as_multiple(value)} is negative"
            " — enterprise value is below zero: a rare deep-value situation"
            " or a data error; verify the inputs."
        )
        falls_outside_normal_range = True
    elif value < 1.0:
        interpretation = (
            f"Enterprise value to sales of {_as_multiple(value)} is below"
            " the roughly 1-3 typical range — cheap per revenue dollar, or a"
            " structurally low-margin business. Margin context is mandatory."
        )
        falls_outside_normal_range = True
    elif value < 3.0:
        interpretation = (
            f"Enterprise value to sales of {_as_multiple(value)} is in the"
            " roughly 1-3 typical range. This is the leverage-corrected"
            " price to sales and the fallback multiple when EBITDA is"
            " negative; margin context is mandatory."
        )
        falls_outside_normal_range = False
    elif value < 10.0:
        interpretation = (
            f"Enterprise value to sales of {_as_multiple(value)} is elevated"
            " (above the roughly 1-3 typical range) — only high margins or"
            " strong growth justify it; check the margin metrics."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Enterprise value to sales of {_as_multiple(value)} is above 10"
            " — unusual: it requires exceptional growth and margins to ever"
            " pay off."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="enterprise_value_to_sales",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_free_cash_flow_yield(value: float | None) -> CalculationInterpretation:
    """Interpret free cash flow / market capitalization."""
    if value is None:
        interpretation = (
            "Not computed — free cash flow or market capitalization was"
            " unavailable. Meaningless for banks; REITs use an"
            " adjusted-funds-from-operations yield."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Free cash flow yield of {_as_percentage(value)} is negative —"
            " the business consumed cash after capital spending. Check"
            " capital_expenditure_intensity: a heavy-reinvestment phase and"
            " value destruction look identical in a single period."
        )
        falls_outside_normal_range = True
    elif value < 0.02:
        interpretation = (
            f"Free cash flow yield of {_as_percentage(value)} is below 2% —"
            " expensive, or a heavy-reinvestment phase; check"
            " capital_expenditure_intensity before calling it overvalued."
        )
        falls_outside_normal_range = True
    elif value < 0.04:
        interpretation = (
            f"Free cash flow yield of {_as_percentage(value)} is modest —"
            " below the 4-8% band considered reasonable. Compare against the"
            " prevailing 10-year Treasury yield."
        )
        falls_outside_normal_range = False
    elif value < 0.08:
        interpretation = (
            f"Free cash flow yield of {_as_percentage(value)} is reasonable"
            " (4-8%). A wide gap versus earnings_yield in either direction"
            " is an accrual-quality flag worth chasing."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Free cash flow yield of {_as_percentage(value)} is above 8% —"
            " value territory, or the market doubts the cash flow's"
            " durability. Cross-check earnings_yield and the leverage"
            " metrics before treating it as a bargain."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="free_cash_flow_yield",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_dividend_yield(value: float | None) -> CalculationInterpretation:
    """Interpret trailing common dividends paid / market capitalization."""
    if value is None:
        interpretation = (
            "Not computed — dividends paid were not reported (an absent"
            " dividend line is not provably a zero flow) or market"
            " capitalization was unavailable."
        )
        falls_outside_normal_range = False
    elif value == 0.0:
        interpretation = (
            "Dividend yield is zero — the company pays no dividend."
            " Uninformative for growth companies, which reinvest instead;"
            " check shareholder_yield for buyback-based capital return."
        )
        falls_outside_normal_range = False
    elif value < 0.02:
        interpretation = (
            f"Dividend yield of {_as_percentage(value)} is a modest payout —"
            " below the roughly 2-4% typical for dividend payers. Read as a"
            " pair with payout_ratio."
        )
        falls_outside_normal_range = False
    elif value < 0.04:
        interpretation = (
            f"Dividend yield of {_as_percentage(value)} is in the roughly"
            " 2-4% band typical for dividend payers. Read as a pair with"
            " payout_ratio."
        )
        falls_outside_normal_range = False
    elif value < 0.06:
        interpretation = (
            f"Dividend yield of {_as_percentage(value)} is elevated — above"
            " the typical 2-4% band but short of the 6-8% level where the"
            " market usually prices a cut. Check payout_ratio for"
            " sustainability."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Dividend yield of {_as_percentage(value)} is above 6% —"
            " usually the market pricing a dividend cut (value-trap"
            " territory) rather than a genuine bargain. Check payout_ratio"
            " and free cash flow cover before trusting the yield."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="dividend_yield",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_payout_ratio(value: float | None) -> CalculationInterpretation:
    """Interpret dividends paid / net income."""
    if value is None:
        interpretation = (
            "Not computed — net income was not positive (the ratio means"
            " nothing against a loss) or dividends were not reported."
            " Compare dividends against free_cash_flow instead."
        )
        falls_outside_normal_range = False
    elif value < 0.30:
        interpretation = (
            f"Payout ratio of {_as_percentage(value)} is low — typical for"
            " growth firms, and at a mature firm it signals capacity to"
            " raise the dividend."
        )
        falls_outside_normal_range = False
    elif value < 0.60:
        interpretation = (
            f"Payout ratio of {_as_percentage(value)} is in the 30-60%"
            " sustainable sweet spot for a mature payer."
        )
        falls_outside_normal_range = False
    elif value < 1.0:
        interpretation = (
            f"Payout ratio of {_as_percentage(value)} is above the 30-60%"
            " sweet spot — the dividend leaves thin earnings cover. Note"
            " REITs structurally run at or above 90% (required"
            " distributions, properly measured against funds from"
            " operations), so sector context matters."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Payout ratio of {_as_percentage(value)} is above 100% — the"
            " company paid out more than it earned, which is unsustainable"
            " outside REIT-style structures; the dividend is being funded"
            " from the balance sheet or borrowings."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="payout_ratio",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_shareholder_yield(value: float | None) -> CalculationInterpretation:
    """Interpret (dividends + buybacks - stock issuance) / market capitalization."""
    if value is None:
        interpretation = (
            "Not computed — dividends, buybacks, or stock issuance were not"
            " reported (absent flows are not provably zero) or market"
            " capitalization was unavailable."
        )
        falls_outside_normal_range = False
    elif value < 0.0:
        interpretation = (
            f"Shareholder yield of {_as_percentage(value)} is negative — the"
            " company is a net issuer of stock, a documented negative"
            " signal. The measure is net of issuance by design, so buybacks"
            " that merely offset stock-compensation dilution don't rescue"
            " it."
        )
        falls_outside_normal_range = True
    elif value < 0.02:
        interpretation = (
            f"Shareholder yield of {_as_percentage(value)} is modest — below"
            " the roughly 2-5% typical for a capital-returning firm."
        )
        falls_outside_normal_range = False
    elif value < 0.05:
        interpretation = (
            f"Shareholder yield of {_as_percentage(value)} is in the roughly"
            " 2-5% band typical for a capital-returning firm."
        )
        falls_outside_normal_range = False
    else:
        interpretation = (
            f"Shareholder yield of {_as_percentage(value)} is above 5% —"
            " aggressive capital return. Check it is funded from free cash"
            " flow rather than borrowings."
        )
        falls_outside_normal_range = True
    return CalculationInterpretation(
        raw_value=value,
        field_name="shareholder_yield",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


# ---------------------------------------------------------------------------
# Composite scores
# ---------------------------------------------------------------------------


def interpret_altman_z_score(value: float | None) -> CalculationInterpretation:
    """Interpret the original Altman (1968) bankruptcy-distress score."""
    if value is None:
        interpretation = (
            "Not computed — an input was missing. The original model applies"
            " only to public manufacturers, so absence is expected outside"
            " that group; never apply it to financials (leverage is their"
            " business model)."
        )
        falls_outside_normal_range = False
    elif value < 1.81:
        interpretation = (
            f"Altman Z-score of {_as_multiple(value)} is in the distress"
            " zone (below 1.81) — the model's historical bankruptcy-warning"
            " range for public manufacturers; treat as a serious flag and"
            " verify the inputs."
        )
        falls_outside_normal_range = True
    elif value <= 2.99:
        interpretation = (
            f"Altman Z-score of {_as_multiple(value)} is in the grey zone"
            " (1.81-2.99) — indeterminate: not predicted distress, but not"
            " clear of it. Read together with the coverage and leverage"
            " metrics."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Altman Z-score of {_as_multiple(value)} is in the safe zone"
            " (above 2.99) — the original 1968 model signals low bankruptcy"
            " risk over the next two years for a public manufacturer."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="altman_z_score",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_altman_z_zone(value: str | None) -> CalculationInterpretation:
    """Interpret the zone label for the original Altman Z-score."""
    if value is None:
        interpretation = (
            "Not computed — an Altman Z-score input was missing. The"
            " original model applies only to public manufacturers, so"
            " absence is expected outside that group; never apply it to"
            " financials."
        )
        falls_outside_normal_range = False
    elif value == calculations.Z_SAFE:
        interpretation = (
            "Altman Z safe zone (score above 2.99): the original 1968 model"
            " signals low bankruptcy risk over the next two years."
        )
        falls_outside_normal_range = False
    elif value == calculations.Z_GREY:
        interpretation = (
            "Altman Z grey zone (score between 1.81 and 2.99):"
            " indeterminate — not predicted distress, but not clear of it."
            " Read together with the coverage and leverage metrics."
        )
        falls_outside_normal_range = True
    elif value == calculations.Z_DISTRESS:
        interpretation = (
            "Altman Z distress zone (score below 1.81): the model's"
            " historical bankruptcy-warning range — treat as a serious flag"
            " and verify the inputs."
        )
        falls_outside_normal_range = True
    else:
        raise ValueError(f"Unrecognized Altman Z zone label: {value!r}")
    return CalculationInterpretation(
        raw_value=value,
        field_name="altman_z_zone",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_altman_z_double_prime(value: float | None) -> CalculationInterpretation:
    """Interpret the Altman Z'' variant for non-manufacturers."""
    if value is None:
        interpretation = (
            "Not computed — an input was missing. The double-prime variant"
            " covers non-manufacturers; never apply it to financials."
        )
        falls_outside_normal_range = False
    elif value < 1.1:
        interpretation = (
            f"Altman Z'' score of {_as_multiple(value)} is in the distress"
            " zone (below 1.1) — the non-manufacturer variant's"
            " bankruptcy-warning range; treat as a serious flag and verify"
            " the inputs."
        )
        falls_outside_normal_range = True
    elif value <= 2.6:
        interpretation = (
            f"Altman Z'' score of {_as_multiple(value)} is in the grey zone"
            " (1.1-2.6) — indeterminate: not predicted distress, but not"
            " clear of it. Read together with the coverage and leverage"
            " metrics."
        )
        falls_outside_normal_range = True
    else:
        interpretation = (
            f"Altman Z'' score of {_as_multiple(value)} is in the safe zone"
            " (above 2.6) — low predicted bankruptcy risk under the"
            " non-manufacturer variant."
        )
        falls_outside_normal_range = False
    return CalculationInterpretation(
        raw_value=value,
        field_name="altman_z_double_prime",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )


def interpret_altman_z_double_prime_zone(value: str | None) -> CalculationInterpretation:
    """Interpret the zone label for the Altman Z'' variant."""
    if value is None:
        interpretation = (
            "Not computed — an Altman Z'' input was missing. The variant"
            " covers non-manufacturers; never apply it to financials."
        )
        falls_outside_normal_range = False
    elif value == calculations.Z_SAFE:
        interpretation = (
            "Altman Z'' safe zone (score above 2.6): low predicted"
            " bankruptcy risk under the non-manufacturer variant."
        )
        falls_outside_normal_range = False
    elif value == calculations.Z_GREY:
        interpretation = (
            "Altman Z'' grey zone (score between 1.1 and 2.6):"
            " indeterminate — not predicted distress, but not clear of it."
            " Read together with the coverage and leverage metrics."
        )
        falls_outside_normal_range = True
    elif value == calculations.Z_DISTRESS:
        interpretation = (
            "Altman Z'' distress zone (score below 1.1): the variant's"
            " bankruptcy-warning range — treat as a serious flag and verify"
            " the inputs."
        )
        falls_outside_normal_range = True
    else:
        raise ValueError(f"Unrecognized Altman Z'' zone label: {value!r}")
    return CalculationInterpretation(
        raw_value=value,
        field_name="altman_z_double_prime_zone",
        interpretation=interpretation,
        falls_outside_normal_range=falls_outside_normal_range,
    )
