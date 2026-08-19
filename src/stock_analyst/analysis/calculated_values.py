"""Calculated results produced by the functions in :mod:`calculations` — the
output counterpart to :class:`quantitative_data.RawQuantitativeData`.

:class:`CalculatedValues` holds one field per calculation in ``calculations.py``,
grouped under the same section banners so the class reads as a table of
contents for that module. Field comments are written for interpretation
agents whose job is to spot unusual values: each gives the definition and
unit, the practitioner reference bands, and the edge cases and sector caveats
that change how a number should be read. They distill
``docs/fundamental_metrics.md``, which remains the full reference.

Conventions carry over from ``calculations.py``:

- Ratios are decimal fractions (0.25 == 25%); day-count metrics are days;
  building blocks (gross profit, total debt, enterprise value, ...) are
  absolute amounts in the filing's currency, except ``earnings_per_share``.
- Flow-based metrics are computed from run-rate annualized values: the
  fiscal-year-to-date flows are multiplied by 4 / quarter number inside
  ``run_all_calculations`` before any metric is computed, so the annual
  reference bands in the field comments apply. Flow/flow ratios
  (margins, coverage, payout) are unaffected by the uniform factor;
  flow-vs-stock and flow-vs-market-cap metrics assume the year so far
  extrapolates, which distorts seasonal businesses early in their fiscal
  year.
- Every field defaults to ``None``, meaning the metric was not computable for
  the given inputs (missing data, zero denominator, or not meaningful per the
  reference doc). Where ``None`` itself carries information — no debt, negative
  book equity — the field comment says so.
- The Altman zone fields hold the ``calculations.Z_SAFE`` / ``Z_GREY`` /
  ``Z_DISTRESS`` strings.
- Calculations that need multiple quarterly reports (average balances,
  prior-period values, period-over-period changes) are descoped until
  multi-report support lands and have no fields here — see
  ``docs/descoped_multi_period_metrics.md`` for the list and how to restore
  them.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CalculatedValues:
    """Every calculated result produced by the functions in ``calculations.py``,
    for a single company at a single point in time.

    Golden rule for interpretation (CFA Institute): almost all ratios are
    only meaningful relative to industry peers and to the company's own
    history. The bands in the field comments are heuristics for flagging,
    not verdicts — "unusual" means verify the inputs and context, not
    automatically bad.
    """

    # ------------------------------------------------------------------
    # Building blocks shared across pillars
    # ------------------------------------------------------------------

    # Revenue minus cost of goods sold, in the filing's currency. Negative
    # means the company sells below direct product cost — a severe flag at any
    # scale. Undefined for banks and insurers (their filings have no cost of
    # goods sold line).
    gross_profit: float | None = None

    # Operating income plus depreciation and amortization (commonly
    # abbreviated EBITDA), in the filing's currency. Negative is severe — the
    # business is not covering even its cash operating costs. Rejected as a
    # concept for banks and insurers.
    earnings_before_interest_taxes_depreciation_and_amortization: float | None = None

    # Income tax expense / pretax income, as a decimal fraction. Roughly
    # 0.15-0.30 is normal for US filers; a rate persistently near zero or
    # above ~0.40 is unusual — look for one-off tax items,
    # valuation-allowance releases, or foreign-rate effects. None when pretax
    # income is not positive (the rate is uninterpretable off a pretax loss).
    effective_tax_rate: float | None = None

    # Operating income times (1 - effective tax rate), commonly abbreviated
    # NOPAT, in the filing's currency. The numerator of return on invested
    # capital; its sign follows operating income.
    net_operating_profit_after_tax: float | None = None

    # All interest-bearing liabilities plus lease obligations, in the
    # filing's currency — deliberately not total liabilities (Damodaran's
    # definition). Zero means debt-free, in which case the coverage and debt
    # ratios are None by design, not missing.
    total_debt: float | None = None

    # Total debt minus cash and marketable securities, in the filing's
    # currency. Negative means a net cash position (common in large
    # technology firms) — leverage risk is essentially nil there regardless
    # of gross debt.
    net_debt: float | None = None

    # Current assets minus current liabilities, in the filing's currency.
    # Absolute dollars, so not comparable across companies — context for the
    # liquidity ratios. Negative is normal and healthy for some retail and
    # subscription models (customers pay before suppliers are paid). Graham's
    # solvency screen: long-term debt should not exceed working capital.
    # Undefined for banks (no current/non-current balance sheet split).
    working_capital: float | None = None

    # Interest-bearing debt plus shareholders' equity minus cash, in the
    # filing's currency — the denominator of return on invested capital.
    # Book capital embeds old accounting choices: past write-offs shrink it
    # and mechanically inflate return on invested capital. Near-zero or
    # negative values make that return uninterpretable.
    invested_capital: float | None = None

    # (Net income - preferred dividends) / weighted-average diluted shares,
    # in currency per share. The level is not comparable across companies
    # (share counts are arbitrary); its uses are the growth series and price
    # ratios. Run-rate annualized from year-to-date earnings.
    earnings_per_share: float | None = None

    # Market capitalization + total debt + preferred equity + minority
    # interest - cash, in the filing's currency. Below market capitalization
    # for net-cash firms; negative (cash exceeding market capitalization plus
    # debt) is a rare deep-value situation or a data error — verify inputs.
    # Enterprise-value multiples are undefined for banks and insurers.
    enterprise_value: float | None = None

    # Operating cash flow minus capital expenditures, in the filing's
    # currency. Positive and growing is good; persistently negative is either
    # growth investment or value destruction — only return on invested
    # capital context distinguishes them. Single-year values are noisy
    # (capital spending is lumpy) and stock-based compensation inflates the
    # operating-cash-flow side. Undefined for banks; REITs use funds from
    # operations instead.
    free_cash_flow: float | None = None

    # ------------------------------------------------------------------
    # Profitability
    # ------------------------------------------------------------------

    # Gross profit / revenue, as a decimal fraction. Cross-industry
    # comparison is nearly meaningless: software runs ~0.70-0.90, retail
    # ~0.20-0.40 — compare against peers and history. An eroding trend is an
    # early warning that competition or input costs are biting; negative is a
    # severe flag at any scale. Undefined for banks and insurers.
    gross_profit_margin: float | None = None

    # Operating income / revenue, as a decimal fraction. Negative means the
    # operations themselves lose money; below 0.05 thin; roughly 0.10-0.20
    # healthy for most industries; above 0.20 strong (the large-cap US median
    # runs in the low-to-mid teens percent); above 0.40 unusual — verify what
    # the filer classifies as operating costs. Not meaningful for banks,
    # where interest is the core operating cost.
    operating_margin: float | None = None

    # Net income / revenue, as a decimal fraction. Negative = net loss;
    # below 0.05 thin; 0.05-0.10 about average; 0.10-0.20 good; above 0.20
    # excellent; above 0.30 unusual — check for one-off gains or tax items
    # before crediting the underlying business. Valid for financials;
    # depressed for REITs by property depreciation.
    net_profit_margin: float | None = None

    # EBITDA / revenue, as a decimal fraction. Rough sector bands: above
    # 0.30-0.40 software/pharma/infrastructure; 0.15-0.25 typical
    # industrials; below 0.10 thin though normal in distribution and retail;
    # negative severe. A comps convenience, not a quality signal —
    # depreciation is a real cost. Not meaningful for financials.
    earnings_before_interest_taxes_depreciation_and_amortization_margin: float | None = None

    # ------------------------------------------------------------------
    # Liquidity (all meaningless for banks and insurers — they file
    # unclassified balance sheets, so the inputs don't exist)
    # ------------------------------------------------------------------

    # Current assets / current liabilities. At or above 1 means short-term
    # assets cover short-term obligations; Graham's defensive standard for
    # industrials is 2.0+. Very high values can signal lazy capital. Inflated
    # by slow-moving inventory and stale receivables, and window-dressable at
    # period end; below 1 is normal and healthy for some retail and
    # subscription models. Meaningless for banks and insurers.
    current_ratio: float | None = None

    # (Cash + short-term investments + receivables) / current liabilities.
    # Around 1 or higher is typically healthy. The real signal is the spread
    # versus the current ratio: a big gap flags an inventory-heavy or
    # inventory-stuck balance sheet. Nearly identical to the current ratio
    # for no-inventory businesses (redundant there). Meaningless for banks.
    quick_ratio: float | None = None

    # (Cash + short-term investments) / current liabilities — the worst-case
    # crisis measure. Healthy firms typically run 0.1-0.5; above 1 means
    # current liabilities are fully covered by cash alone — an idle-cash
    # hoard or a deliberate war chest (read with the capital-return metrics).
    # Meaningless for banks.
    cash_ratio: float | None = None

    # Operating cash flow / current liabilities. Above 1 means operations
    # alone cover short-term obligations. The strongest liquidity cross-check
    # because it is flow-based and much harder to window-dress than
    # balance-sheet snapshots. Not meaningful for banks (loan and deposit
    # flows distort it).
    operating_cash_flow_ratio: float | None = None

    # Days the firm can operate on liquid assets with zero revenue. Above 90
    # days comfortable; 30-90 adequate; below 30 tight — the firm depends on
    # near-term revenue or financing to keep operating.
    defensive_interval_ratio: float | None = None

    # ------------------------------------------------------------------
    # Solvency & leverage
    # ------------------------------------------------------------------

    # Total debt / shareholders' equity. Below 1.0 is a common conservative
    # screen for industrials, but sector norms dominate — utilities and REITs
    # run high by design, and financials are structurally high (debt is their
    # raw material). None when equity is not positive (common in
    # buyback-heavy large-caps) — fall back to debt_to_capital, which stays
    # bounded.
    debt_to_equity: float | None = None

    # Total debt / total assets, bounded 0-1 so it stays well-behaved when
    # equity is thin or negative. Above 0.5 means the asset base is majority
    # debt-funded.
    debt_to_assets: float | None = None

    # Total debt / (total debt + equity) — the form credit analysts prefer,
    # bounded 0-1. For non-financials: below 0.3-0.4 conservative; 0.4-0.6
    # moderate; above 0.6 aggressive.
    debt_to_capital: float | None = None

    # Net debt / EBITDA — years of EBITDA needed to repay net debt, the
    # lender's first screen. Credit-practice tiers: below 1.5 minimal risk;
    # 2-3 intermediate; 3-4 significant (a common covenant ceiling); above
    # 4-5 highly leveraged. Negative means net cash — a strength, not
    # distress. None when EBITDA is not positive. Peak-cycle EBITDA flatters
    # the ratio. REITs run 5-7 on their industry variant; meaningless for
    # banks.
    net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization: float | None = None

    # Operating income / gross interest expense. Damodaran's synthetic-rating
    # map for large non-financials: 8.5+ ≈ AAA; 3-4.25 ≈ A-; above 5
    # comfortable; below 1.5-2 distress territory. None when interest expense
    # is zero or negative — that means no debt, a good sign rather than
    # missing data. Not meaningful for banks (interest is their core
    # operating cost).
    interest_coverage: float | None = None

    # EBITDA / interest expense — the more generous coverage variant (adds
    # back depreciation and amortization), so it runs above the
    # operating-income form by construction. Credit practice: above 6
    # comfortable; 2-6 intermediate; below 2 stressed.
    earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage: float | None = (
        None
    )

    # Operating cash flow / total debt — internally generated cash against
    # the whole debt stack. Roughly above 0.40 is associated with strong
    # investment-grade credit. None when total debt is zero (debt-free).
    operating_cash_flow_to_debt: float | None = None

    # ------------------------------------------------------------------
    # Cash flow - generation & quality
    # ------------------------------------------------------------------

    # Free cash flow / revenue, as a decimal fraction — cash-based
    # profitability, the check on the accrual margin waterfall. Above 0.10
    # generally strong; software leaders above 0.20; manufacturing 0.10-0.15;
    # single digits (below 0.10) normal in retail. Smooth over multiple years
    # — capital spending is lumpy.
    free_cash_flow_margin: float | None = None

    # Operating cash flow / net income — the consensus earnings-quality
    # check. Persistently at or above 1 means earnings backed by cash
    # (depreciation alone should push most firms above 1); persistently below
    # 1 means accrual-driven earnings. One bad year is noise (working-capital
    # timing). None when net income is not positive — the ratio explodes near
    # zero; use the Sloan accruals ratio instead.
    operating_cash_flow_to_net_income: float | None = None

    # (Net income - operating cash flow - investing cash flow) / total
    # assets. Between -0.10 and +0.10 is considered safe; above +0.25 is a
    # strong warning — high-accrual firms systematically underperform (Sloan
    # 1996). The asset-scaled form to prefer when net income is near zero.
    # Flow inputs are run-rate annualized from year-to-date figures.
    sloan_accruals_ratio: float | None = None

    # Free cash flow / EBITDA. At or above 0.8 strong; ~1.0 ideal; above 1
    # is usually a temporary working-capital benefit, not a durable feature.
    # None when EBITDA is not positive.
    free_cash_flow_conversion: float | None = None

    # Capital expenditures / revenue, as a decimal fraction. Below 0.05
    # asset-light; above 0.15 capital-intensive. Lumpy — average over 3-5
    # years. High spending is only bad when the returns on it (return on
    # invested capital) are poor.
    capital_expenditure_intensity: float | None = None

    # Capital expenditures / depreciation and amortization. Above 1 =
    # growing asset base; below 1 = possible underinvestment (a rough
    # maintenance-spending proxy) and, if sustained, an aging asset base.
    capital_expenditures_to_depreciation: float | None = None

    # ------------------------------------------------------------------
    # Growth
    # ------------------------------------------------------------------

    # 1 - payout ratio: the share of earnings reinvested. Near 1 typical for
    # growth firms (paying no dividend); near 0 means nearly all earnings are
    # paid out.
    retention_rate: float | None = None

    # ------------------------------------------------------------------
    # Valuation
    # ------------------------------------------------------------------

    # Market capitalization / run-rate annualized net income (year-to-date
    # earnings scaled to a full year — seasonal businesses look distorted
    # early in the fiscal year). Long-run US market average is roughly 15-20.
    # Below 10 = priced for decline or deep value — verify earnings are not
    # at a cyclical peak (for cyclicals the ratio is lowest exactly at the
    # earnings peak); 20-30 growth premium; above 50 speculative growth
    # pricing or a trough-earnings artifact — inspect the earnings, don't
    # just call it expensive. None when earnings are not positive — rank on
    # earnings_yield instead. Misleading for REITs (price to funds from
    # operations is the substitute).
    price_to_earnings: float | None = None

    # Net income / market capitalization — the price-to-earnings inverse,
    # but defined even for negative earnings so it ranks the full universe.
    # Compare against the 10-year Treasury yield: a yield below the risk-free
    # rate means the price is justified only by expected growth. Run-rate
    # annualized from year-to-date earnings.
    earnings_yield: float | None = None

    # Operating income / enterprise value — Greenblatt's
    # capital-structure-neutral earnings yield. Above ~0.10 is classic cheap
    # territory. Inapplicable to financials. Run-rate annualized from
    # year-to-date operating income.
    earnings_before_interest_and_taxes_to_enterprise_value: float | None = None

    # Market capitalization / common book equity. Below 1 means trading
    # below accounting net worth; the justified level rises with return on
    # equity — always read the pair. Historical-cost accounting and expensed
    # intangibles understate true equity for asset-light firms, so it says
    # little about software companies. None when book equity is not positive.
    # The most meaningful multiple for banks and insurers.
    price_to_book: float | None = None

    # Market capitalization / run-rate annualized revenue (year-to-date
    # revenue scaled to a full year — seasonal businesses look distorted
    # early in the fiscal year). Below 1 cheap per revenue dollar (or a
    # low-margin business); ~1-2 typical for a mature company; above 10
    # demands exceptional growth plus high margins. Must be read jointly with
    # net margin — a high-margin and a zero-margin firm at the same multiple
    # are not equally valued. Not for financials.
    price_to_sales: float | None = None

    # Enterprise value / EBITDA — the standard operating multiple across
    # capital structures. Broad market typically ~8-12; below 6 cheap (or
    # the market is pricing decline); above 15 rich or growth-priced for a
    # mature firm. Ignores capital spending, so it flatters capital-intensive
    # firms — cross-check the operating-income form. None when EBITDA is not
    # positive — fall back to enterprise value to sales. Never for
    # financials. Run-rate annualized from year-to-date EBITDA.
    enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization: (
        float | None
    ) = None

    # Enterprise value / operating income. Typically ~10-14; below 10 (its
    # inverse above 0.10) is classic Greenblatt-cheap territory. Charges for
    # depreciation, so prefer it over the EBITDA form when comparing firms of
    # different capital intensity. Not for financials. Run-rate annualized
    # from year-to-date operating income.
    enterprise_value_to_earnings_before_interest_and_taxes: float | None = None

    # Enterprise value / run-rate annualized revenue — the leverage-corrected
    # price-to-sales, and the fallback when EBITDA is negative. Roughly 1-3
    # typical; above 10 unusual (requires exceptional growth and margins).
    # Margin context is mandatory. Not for financials.
    enterprise_value_to_sales: float | None = None

    # Free cash flow / market capitalization, as a decimal fraction. Above
    # 0.08 value territory (or the market doubts the cash flow's
    # durability); 0.04-0.08 reasonable; below 0.02 expensive or a
    # heavy-reinvestment phase — check capital expenditure intensity before
    # calling it overvalued. A wide gap versus earnings yield is itself an
    # accrual-quality flag. Compare against the 10-year Treasury yield.
    # Meaningless for banks; REITs use an adjusted-funds-from-operations
    # yield. Run-rate annualized from year-to-date cash flows.
    free_cash_flow_yield: float | None = None

    # Run-rate annualized common dividends paid / market capitalization, as
    # a decimal fraction. Roughly 0.02-0.04 typical for dividend payers;
    # above 0.06-0.08 usually means the market is pricing a cut (value-trap
    # territory). Zero is uninformative for no-dividend growth companies.
    # Read as a pair with the payout ratio.
    dividend_yield: float | None = None

    # Dividends paid / net income, as a decimal fraction. 0.30-0.60 is the
    # sustainable sweet spot for a mature payer; above 1 (or above free cash
    # flow) is unsustainable; very low at a mature firm signals capacity to
    # raise. None when net income is not positive — compare dividends against
    # free cash flow instead. REITs structurally run at or above 0.90
    # (required distributions), measured against funds from operations.
    payout_ratio: float | None = None

    # (Dividends + buybacks - stock issuance) / market capitalization, as a
    # decimal fraction. Roughly 0.02-0.05 typical for a capital-returning
    # firm; above 0.05 aggressive capital return; negative means a net
    # issuer — a documented negative signal. Net of issuance by design, so
    # buybacks that merely offset stock-compensation dilution don't count.
    # Run-rate annualized from year-to-date flows — a single large buyback
    # early in the year extrapolates.
    shareholder_yield: float | None = None

    # ------------------------------------------------------------------
    # Composite scores
    # ------------------------------------------------------------------

    # Altman (1968) bankruptcy-distress score, original model — for public
    # manufacturers only. Above 2.99 safe; 1.81-2.99 grey zone; below 1.81
    # distress. Never apply to financials (leverage is their business model);
    # use the double-prime variant for other non-manufacturers. Flow terms
    # (operating income, revenue) are run-rate annualized from year-to-date
    # figures.
    altman_z_score: float | None = None

    # Zone label for altman_z_score: 'safe' (> 2.99), 'grey', or 'distress' (< 1.81).
    altman_z_zone: str | None = None

    # Altman Z'' variant for non-manufacturers (book equity in the fourth
    # term, asset turnover dropped). Above 2.6 safe; 1.1-2.6 grey zone;
    # below 1.1 distress. Never apply to financials. The operating-income
    # term is run-rate annualized from year-to-date figures.
    altman_z_double_prime: float | None = None

    # Zone label for altman_z_double_prime: 'safe' (> 2.6), 'grey', or 'distress' (< 1.1).
    altman_z_double_prime_zone: str | None = None
