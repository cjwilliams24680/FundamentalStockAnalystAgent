"""Calculated results produced by the functions in :mod:`metrics` — the
output counterpart to :class:`quarterly_report_parse_result.QuarterlyReportParseResult`.

:class:`CalculatedMetrics` holds one field per calculation in ``metrics.py``,
grouped under the same section banners so the class reads as a table of
contents for that module. Field descriptions are written for interpretation
agents whose job is to spot unusual values: each gives the definition and
unit, the practitioner reference bands, and the edge cases and sector caveats
that change how a number should be read. They distill
``docs/fundamental_metrics.md``, which remains the full reference.

Conventions carry over from ``metrics.py``:

- Ratios are decimal fractions (0.25 == 25%); day-count metrics are days;
  building blocks (gross profit, total debt, enterprise value, ...) are
  absolute amounts in the filing's currency, except ``earnings_per_share``.
- Every field defaults to ``None``, meaning the metric was not computable for
  the given inputs (missing data, zero denominator, or not meaningful per the
  reference doc). Where ``None`` itself carries information — no debt, negative
  book equity — the field description says so.
- The four ``..._growth`` fields are year-over-year applications of
  :func:`metrics.growth_rate` to revenue, earnings per share, operating
  income, and free cash flow (the series named in docs section 7).
  :func:`metrics.compound_annual_growth_rate` has no field here — it needs
  multi-year history beyond a single report pair.
- Composite scores nest the result classes defined in ``metrics.py``
  (per-signal and per-factor detail preserved); the Altman zone fields hold
  the ``metrics.Z_SAFE`` / ``Z_GREY`` / ``Z_DISTRESS`` strings.
"""

from pydantic import BaseModel, ConfigDict, Field

from metrics import BeneishResult, DuPontFiveFactor, DuPontThreeFactor, FScoreResult


class CalculatedMetrics(BaseModel):
    """Every calculated result produced by the functions in ``metrics.py``,
    for a single company at a single point in time.

    Golden rule for interpretation (CFA Institute): almost all ratios are
    only meaningful relative to industry peers and to the company's own
    history. The bands in the field descriptions are heuristics for flagging,
    not verdicts — "unusual" means verify the inputs and context, not
    automatically bad.
    """

    model_config = ConfigDict(frozen=True)

    # ------------------------------------------------------------------
    # Building blocks shared across pillars
    # ------------------------------------------------------------------

    gross_profit: float | None = Field(
        default=None,
        description=(
            "Revenue minus cost of goods sold, in the filing's currency."
            " Negative means the company sells below direct product cost — a"
            " severe flag at any scale. Undefined for banks and insurers"
            " (their filings have no cost of goods sold line)."
        ),
    )
    earnings_before_interest_taxes_depreciation_and_amortization: float | None = Field(
        default=None,
        description=(
            "Operating income plus depreciation and amortization (commonly"
            " abbreviated EBITDA), in the filing's currency. Negative is"
            " severe — the business is not covering even its cash operating"
            " costs. Rejected as a concept for banks and insurers."
        ),
    )
    effective_tax_rate: float | None = Field(
        default=None,
        description=(
            "Income tax expense / pretax income, as a decimal fraction."
            " Roughly 0.15-0.30 is normal for US filers; a rate persistently"
            " near zero or above ~0.40 is unusual — look for one-off tax"
            " items, valuation-allowance releases, or foreign-rate effects."
            " None when pretax income is not positive (the rate is"
            " uninterpretable off a pretax loss)."
        ),
    )
    net_operating_profit_after_tax: float | None = Field(
        default=None,
        description=(
            "Operating income times (1 - effective tax rate), commonly"
            " abbreviated NOPAT, in the filing's currency. The numerator of"
            " return on invested capital; its sign follows operating income."
        ),
    )
    total_debt: float | None = Field(
        default=None,
        description=(
            "All interest-bearing liabilities plus lease obligations, in the"
            " filing's currency — deliberately not total liabilities"
            " (Damodaran's definition). Zero means debt-free, in which case"
            " the coverage and debt ratios are None by design, not missing."
        ),
    )
    net_debt: float | None = Field(
        default=None,
        description=(
            "Total debt minus cash and marketable securities, in the"
            " filing's currency. Negative means a net cash position (common"
            " in large technology firms) — leverage risk is essentially nil"
            " there regardless of gross debt."
        ),
    )
    working_capital: float | None = Field(
        default=None,
        description=(
            "Current assets minus current liabilities, in the filing's"
            " currency. Absolute dollars, so not comparable across companies"
            " — context for the liquidity ratios. Negative is normal and"
            " healthy for some retail and subscription models (customers pay"
            " before suppliers are paid). Graham's solvency screen: long-term"
            " debt should not exceed working capital. Undefined for banks"
            " (no current/non-current balance sheet split)."
        ),
    )
    invested_capital: float | None = Field(
        default=None,
        description=(
            "Interest-bearing debt plus shareholders' equity minus cash, in"
            " the filing's currency — the denominator of return on invested"
            " capital. Book capital embeds old accounting choices: past"
            " write-offs shrink it and mechanically inflate return on"
            " invested capital. Near-zero or negative values make that"
            " return uninterpretable."
        ),
    )
    earnings_per_share: float | None = Field(
        default=None,
        description=(
            "(Net income - preferred dividends) / weighted-average shares,"
            " in currency per share. The level is not comparable across"
            " companies (share counts are arbitrary); its uses are the"
            " growth series and price ratios."
        ),
    )
    enterprise_value: float | None = Field(
        default=None,
        description=(
            "Market capitalization + total debt + preferred equity +"
            " minority interest - cash, in the filing's currency. Below"
            " market capitalization for net-cash firms; negative (cash"
            " exceeding market capitalization plus debt) is a rare deep-value"
            " situation or a data error — verify inputs. Enterprise-value"
            " multiples are undefined for banks and insurers."
        ),
    )
    free_cash_flow: float | None = Field(
        default=None,
        description=(
            "Operating cash flow minus capital expenditures, in the filing's"
            " currency. Positive and growing is good; persistently negative"
            " is either growth investment or value destruction — only return"
            " on invested capital context distinguishes them. Single-year"
            " values are noisy (capital spending is lumpy) and stock-based"
            " compensation inflates the operating-cash-flow side. Undefined"
            " for banks; REITs use funds from operations instead."
        ),
    )

    # ------------------------------------------------------------------
    # Profitability
    # ------------------------------------------------------------------

    gross_profit_margin: float | None = Field(
        default=None,
        description=(
            "Gross profit / revenue, as a decimal fraction. Cross-industry"
            " comparison is nearly meaningless: software runs ~0.70-0.90,"
            " retail ~0.20-0.40 — compare against peers and history."
            " An eroding trend is an early warning that competition or input"
            " costs are biting; negative is a severe flag at any scale."
            " Undefined for banks and insurers."
        ),
    )
    operating_margin: float | None = Field(
        default=None,
        description=(
            "Operating income / revenue, as a decimal fraction. Negative"
            " means the operations themselves lose money; below 0.05 thin;"
            " roughly 0.10-0.20 healthy for most industries; above 0.20"
            " strong (the large-cap US median runs in the low-to-mid teens"
            " percent); above 0.40 unusual — verify what the filer classifies"
            " as operating costs. Not meaningful for banks, where interest is"
            " the core operating cost."
        ),
    )
    net_profit_margin: float | None = Field(
        default=None,
        description=(
            "Net income / revenue, as a decimal fraction. Negative = net"
            " loss; below 0.05 thin; 0.05-0.10 about average; 0.10-0.20"
            " good; above 0.20 excellent; above 0.30 unusual — check for"
            " one-off gains or tax items before crediting the underlying"
            " business. Valid for financials; depressed for REITs by"
            " property depreciation."
        ),
    )
    earnings_before_interest_taxes_depreciation_and_amortization_margin: float | None = Field(
        default=None,
        description=(
            "EBITDA / revenue, as a decimal fraction. Rough sector bands:"
            " above 0.30-0.40 software/pharma/infrastructure; 0.15-0.25"
            " typical industrials; below 0.10 thin though normal in"
            " distribution and retail; negative severe. A comps convenience,"
            " not a quality signal — depreciation is a real cost. Not"
            " meaningful for financials."
        ),
    )
    return_on_equity: float | None = Field(
        default=None,
        description=(
            "Net income / average shareholders' equity, as a decimal"
            " fraction. Sustained ~0.15+ is the common quality bar. Never"
            " read alone: it is mechanically inflated by leverage — check"
            " the DuPont decomposition's equity multiplier to see whether it"
            " is operationally earned. None when average equity is not"
            " positive (common after heavy buybacks) — fall back to return"
            " on invested capital. The primary profitability metric for"
            " banks and insurers."
        ),
    )
    return_on_assets: float | None = Field(
        default=None,
        description=(
            "Net income / average total assets, as a decimal fraction. For"
            " non-financials above 0.05 is good and above 0.10 excellent."
            " Banks run on a different scale entirely: ~0.01+ is the classic"
            " good-bank threshold. One of the few return metrics that works"
            " for banks."
        ),
    )
    return_on_invested_capital: float | None = Field(
        default=None,
        description=(
            "Net operating profit after tax / average invested capital"
            " (commonly abbreviated ROIC), as a decimal fraction. Anchor to"
            " the cost of capital (typical large-cap weighted average cost"
            " of capital is ~0.08-0.10): below 0.08 likely value-destroying;"
            " 0.10-0.15 solid; above 0.15 durable-competitive-advantage"
            " territory; above 0.40 unusual — usually book capital shrunken"
            " by past write-offs rather than superhuman economics. Growth"
            " only creates value when this exceeds the cost of capital."
            " Undefined for financials — use return on equity there."
        ),
    )

    # ------------------------------------------------------------------
    # Efficiency
    # ------------------------------------------------------------------

    total_asset_turnover: float | None = Field(
        default=None,
        description=(
            "Revenue / average total assets — revenue per dollar of assets."
            " Most non-financials fall roughly 0.5-2.0; below 0.25 outside"
            " utilities and real estate is unusual (idle assets or an"
            " overvalued asset base). A low value can just mean capital"
            " intensity, not inefficiency — peer-relative only. Trivially"
            " tiny (~0.03-0.1) and signal-free for banks."
        ),
    )
    fixed_asset_turnover: float | None = Field(
        default=None,
        description=(
            "Revenue / average net fixed assets. Capital-intensive firms"
            " typically run ~1-4; only meaningful there. Mechanically rises"
            " as assets depreciate, so a high or rising value alongside flat"
            " capital spending is an aging-asset-base artifact — check"
            " capital expenditures to depreciation before crediting"
            " efficiency. Noise for services, software, and financials."
        ),
    )
    working_capital_turnover: float | None = Field(
        default=None,
        description=(
            "Revenue / average working capital. None when average working"
            " capital is not positive — which is common and makes the ratio"
            " uninterpretable (the cash conversion cycle is the better"
            " lens). Where defined, higher = leaner funding of operations;"
            " above ~10 is unusually high — a thin working-capital buffer or"
            " a structurally negative-working-capital model; cross-check the"
            " liquidity ratios."
        ),
    )
    days_inventory_on_hand: float | None = Field(
        default=None,
        description=(
            "Days of inventory held (365 / inventory turnover). Level"
            " varies widely by industry; the signal is the trend — rising"
            " days flag obsolescence risk or demand weakness. None for"
            " businesses without inventory (software, services), which is"
            " legitimate, not missing data."
        ),
    )
    days_sales_outstanding: float | None = Field(
        default=None,
        description=(
            "Days to collect receivables (365 / receivables turnover)."
            " Roughly 30-60 days typical; above 90 unusual — collection"
            " problems or channel stuffing. Rising faster than revenue is a"
            " classic aggressive-revenue-recognition red flag."
        ),
    )
    purchases: float | None = Field(
        default=None,
        description=(
            "Cost of goods sold plus the change in inventory, in the"
            " filing's currency — an approximation used as the denominator"
            " basis for days payables outstanding. An intermediate, not a"
            " metric to interpret on its own."
        ),
    )
    days_payables_outstanding: float | None = Field(
        default=None,
        description=(
            "Days taken to pay suppliers (365 / payables turnover). Roughly"
            " 30-60 days typical. High is ambiguous — supplier bargaining"
            " power or payment distress — triangulate with the liquidity"
            " ratios before reading it either way."
        ),
    )
    cash_conversion_cycle: float | None = Field(
        default=None,
        description=(
            "Days inventory + days sales outstanding - days payables"
            " outstanding: days of cash tied up between paying suppliers"
            " and collecting from customers. Roughly 30-90 days common for"
            " manufacturers and retailers; lower is better; negative means"
            " suppliers finance the operation — a structural advantage, not"
            " a flag. Undefined for financials and REITs; degenerate for"
            " no-inventory businesses."
        ),
    )

    # ------------------------------------------------------------------
    # Liquidity (all meaningless for banks and insurers — they file
    # unclassified balance sheets, so the inputs don't exist)
    # ------------------------------------------------------------------

    current_ratio: float | None = Field(
        default=None,
        description=(
            "Current assets / current liabilities. At or above 1 means"
            " short-term assets cover short-term obligations; Graham's"
            " defensive standard for industrials is 2.0+. Very high values"
            " can signal lazy capital. Inflated by slow-moving inventory and"
            " stale receivables, and window-dressable at period end; below 1"
            " is normal and healthy for some retail and subscription models."
            " Meaningless for banks and insurers."
        ),
    )
    quick_ratio: float | None = Field(
        default=None,
        description=(
            "(Cash + short-term investments + receivables) / current"
            " liabilities. Around 1 or higher is typically healthy. The"
            " real signal is the spread versus the current ratio: a big gap"
            " flags an inventory-heavy or inventory-stuck balance sheet."
            " Nearly identical to the current ratio for no-inventory"
            " businesses (redundant there). Meaningless for banks."
        ),
    )
    cash_ratio: float | None = Field(
        default=None,
        description=(
            "(Cash + short-term investments) / current liabilities — the"
            " worst-case crisis measure. Healthy firms typically run"
            " 0.1-0.5; above 1 means current liabilities are fully covered"
            " by cash alone — an idle-cash hoard or a deliberate war chest"
            " (read with the capital-return metrics). Meaningless for banks."
        ),
    )
    operating_cash_flow_ratio: float | None = Field(
        default=None,
        description=(
            "Operating cash flow / current liabilities. Above 1 means"
            " operations alone cover short-term obligations. The strongest"
            " liquidity cross-check because it is flow-based and much harder"
            " to window-dress than balance-sheet snapshots. Not meaningful"
            " for banks (loan and deposit flows distort it)."
        ),
    )
    defensive_interval_ratio: float | None = Field(
        default=None,
        description=(
            "Days the firm can operate on liquid assets with zero revenue."
            " Above 90 days comfortable; 30-90 adequate; below 30 tight —"
            " the firm depends on near-term revenue or financing to keep"
            " operating."
        ),
    )

    # ------------------------------------------------------------------
    # Solvency & leverage
    # ------------------------------------------------------------------

    debt_to_equity: float | None = Field(
        default=None,
        description=(
            "Total debt / shareholders' equity. Below 1.0 is a common"
            " conservative screen for industrials, but sector norms dominate"
            " — utilities and REITs run high by design, and financials are"
            " structurally high (debt is their raw material). None when"
            " equity is not positive (common in buyback-heavy large-caps) —"
            " fall back to debt_to_capital, which stays bounded."
        ),
    )
    debt_to_assets: float | None = Field(
        default=None,
        description=(
            "Total debt / total assets, bounded 0-1 so it stays"
            " well-behaved when equity is thin or negative. Above 0.5 means"
            " the asset base is majority debt-funded."
        ),
    )
    debt_to_capital: float | None = Field(
        default=None,
        description=(
            "Total debt / (total debt + equity) — the form credit analysts"
            " prefer, bounded 0-1. For non-financials: below 0.3-0.4"
            " conservative; 0.4-0.6 moderate; above 0.6 aggressive."
        ),
    )
    financial_leverage: float | None = Field(
        default=None,
        description=(
            "Average total assets / average total equity (the equity"
            " multiplier — the leverage leg of the DuPont decomposition;"
            " captures all liabilities, not just debt). Around 2-3 is"
            " typical for non-financials; above 5 is high — or a"
            " buyback-shrunken equity base, so check book equity before"
            " reading it as debt risk. Banks structurally run ~8-15, and"
            " this is the leverage measure that stays meaningful for them."
        ),
    )
    net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization: float | None = Field(
        default=None,
        description=(
            "Net debt / EBITDA — years of EBITDA needed to repay net debt,"
            " the lender's first screen. Credit-practice tiers: below 1.5"
            " minimal risk; 2-3 intermediate; 3-4 significant (a common"
            " covenant ceiling); above 4-5 highly leveraged. Negative means"
            " net cash — a strength, not distress. None when EBITDA is not"
            " positive. Peak-cycle EBITDA flatters the ratio. REITs run 5-7"
            " on their industry variant; meaningless for banks."
        ),
    )
    interest_coverage: float | None = Field(
        default=None,
        description=(
            "Operating income / gross interest expense. Damodaran's"
            " synthetic-rating map for large non-financials: 8.5+ ≈ AAA;"
            " 3-4.25 ≈ A-; above 5 comfortable; below 1.5-2 distress"
            " territory. None when interest expense is zero or negative —"
            " that means no debt, a good sign rather than missing data. Not"
            " meaningful for banks (interest is their core operating cost)."
        ),
    )
    earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage: float | None = Field(
        default=None,
        description=(
            "EBITDA / interest expense — the more generous coverage variant"
            " (adds back depreciation and amortization), so it runs above"
            " the operating-income form by construction. Credit practice:"
            " above 6 comfortable; 2-6 intermediate; below 2 stressed."
        ),
    )
    operating_cash_flow_to_debt: float | None = Field(
        default=None,
        description=(
            "Operating cash flow / total debt — internally generated cash"
            " against the whole debt stack. Roughly above 0.40 is"
            " associated with strong investment-grade credit. None when"
            " total debt is zero (debt-free)."
        ),
    )

    # ------------------------------------------------------------------
    # Cash flow - generation & quality
    # ------------------------------------------------------------------

    free_cash_flow_margin: float | None = Field(
        default=None,
        description=(
            "Free cash flow / revenue, as a decimal fraction — cash-based"
            " profitability, the check on the accrual margin waterfall."
            " Above 0.10 generally strong; software leaders above 0.20;"
            " manufacturing 0.10-0.15; single digits (below 0.10) normal in"
            " retail. Smooth over multiple years — capital spending is"
            " lumpy."
        ),
    )
    operating_cash_flow_to_net_income: float | None = Field(
        default=None,
        description=(
            "Operating cash flow / net income — the consensus"
            " earnings-quality check. Persistently at or above 1 means"
            " earnings backed by cash (depreciation alone should push most"
            " firms above 1); persistently below 1 means accrual-driven"
            " earnings. One bad year is noise (working-capital timing)."
            " None when net income is not positive — the ratio explodes"
            " near zero; use the Sloan accruals ratio instead."
        ),
    )
    sloan_accruals_ratio: float | None = Field(
        default=None,
        description=(
            "(Net income - operating cash flow - investing cash flow) /"
            " total assets. Between -0.10 and +0.10 is considered safe;"
            " above +0.25 is a strong warning — high-accrual firms"
            " systematically underperform (Sloan 1996). The asset-scaled"
            " form to prefer when net income is near zero."
        ),
    )
    free_cash_flow_conversion: float | None = Field(
        default=None,
        description=(
            "Free cash flow / EBITDA. At or above 0.8 strong; ~1.0 ideal;"
            " above 1 is usually a temporary working-capital benefit, not a"
            " durable feature. None when EBITDA is not positive."
        ),
    )
    capital_expenditure_intensity: float | None = Field(
        default=None,
        description=(
            "Capital expenditures / revenue, as a decimal fraction."
            " Below 0.05 asset-light; above 0.15 capital-intensive. Lumpy —"
            " average over 3-5 years. High spending is only bad when the"
            " returns on it (return on invested capital) are poor."
        ),
    )
    capital_expenditures_to_depreciation: float | None = Field(
        default=None,
        description=(
            "Capital expenditures / depreciation and amortization. Above 1"
            " = growing asset base; below 1 = possible underinvestment (a"
            " rough maintenance-spending proxy). Read alongside fixed asset"
            " turnover to catch an aging asset base masquerading as"
            " efficiency."
        ),
    )

    # ------------------------------------------------------------------
    # Growth
    # ------------------------------------------------------------------

    revenue_growth: float | None = Field(
        default=None,
        description=(
            "Year-over-year revenue growth, as a decimal fraction. Negative"
            " = contraction (distinguish a cyclical dip from secular"
            " decline); 0-0.05 mature/GDP-pace; 0.05-0.15 healthy; above"
            " 0.20 high growth; above 0.40 sustained is rare — verify it is"
            " not acquisition-driven. Growth rates fade toward ~0.02-0.05"
            " nominal over time regardless of industry, so extrapolating"
            " high growth is the classic error."
        ),
    )
    earnings_per_share_growth: float | None = Field(
        default=None,
        description=(
            "Year-over-year growth in earnings per share, as a decimal"
            " fraction. Around 0.10+ sustained is strong; above 0.25 rarely"
            " persists. None when the base year is not meaningfully positive"
            " (growth off a loss is meaningless). Growth driven by buybacks"
            " without operating-income growth is lower quality — compare"
            " revenue, operating income, and per-share growth side by side."
        ),
    )
    operating_income_growth: float | None = Field(
        default=None,
        description=(
            "Year-over-year operating income growth, as a decimal fraction."
            " The intermediate step: versus revenue growth it exposes"
            " operating leverage; versus earnings-per-share growth it"
            " exposes financing and tax effects. None off a non-positive"
            " base year."
        ),
    )
    free_cash_flow_growth: float | None = Field(
        default=None,
        description=(
            "Year-over-year free cash flow growth, as a decimal fraction."
            " Validates whether earnings growth is cash-backed. Too noisy to"
            " lead the analysis (capital-spending timing, working-capital"
            " swings) — smooth over multiple years. None off a non-positive"
            " base year."
        ),
    )
    retention_rate: float | None = Field(
        default=None,
        description=(
            "1 - payout ratio: the share of earnings reinvested. Near 1"
            " typical for growth firms (paying no dividend); near 0 means"
            " nearly all earnings are paid out."
        ),
    )
    sustainable_growth_rate: float | None = Field(
        default=None,
        description=(
            "Retention rate times return on equity — the growth fundable"
            " from retained earnings without new capital. Read as a"
            " comparison, not a level: actual growth persistently above it"
            " means expect share issuance or rising leverage to fund the"
            " gap; growth well below it with high return on equity means"
            " capacity to raise dividends or buybacks."
        ),
    )
    reinvestment_rate: float | None = Field(
        default=None,
        description=(
            "(Net capital expenditures + change in working capital) / net"
            " operating profit after tax (Damodaran). Can exceed 1"
            " (investing more than after-tax operating profit) or be"
            " negative (shrinking the asset base). Lumpy — average over"
            " several years before reading it. None when net operating"
            " profit after tax is not positive. Not computable for"
            " financials."
        ),
    )
    fundamental_growth: float | None = Field(
        default=None,
        description=(
            "Reinvestment rate times return on invested capital — expected"
            " operating-income growth from the value-driver identity. A"
            " modeled quantity, not a screened one: compare against actual"
            " growth as a plausibility check."
        ),
    )

    # ------------------------------------------------------------------
    # Valuation
    # ------------------------------------------------------------------

    price_to_earnings: float | None = Field(
        default=None,
        description=(
            "Market capitalization / trailing net income. Long-run US"
            " market average is roughly 15-20. Below 10 = priced for"
            " decline or deep value — verify earnings are not at a cyclical"
            " peak (for cyclicals the ratio is lowest exactly at the"
            " earnings peak); 20-30 growth premium; above 50 speculative"
            " growth pricing or a trough-earnings artifact — inspect the"
            " earnings, don't just call it expensive. None when earnings"
            " are not positive — rank on earnings_yield instead. Misleading"
            " for REITs (price to funds from operations is the substitute)."
        ),
    )
    earnings_yield: float | None = Field(
        default=None,
        description=(
            "Net income / market capitalization — the price-to-earnings"
            " inverse, but defined even for negative earnings so it ranks"
            " the full universe. Compare against the 10-year Treasury"
            " yield: a yield below the risk-free rate means the price is"
            " justified only by expected growth."
        ),
    )
    earnings_before_interest_and_taxes_to_enterprise_value: float | None = Field(
        default=None,
        description=(
            "Operating income / enterprise value — Greenblatt's"
            " capital-structure-neutral earnings yield. Above ~0.10 is"
            " classic cheap territory. Inapplicable to financials."
        ),
    )
    price_to_book: float | None = Field(
        default=None,
        description=(
            "Market capitalization / common book equity. Below 1 means"
            " trading below accounting net worth; the justified level rises"
            " with return on equity — always read the pair. Historical-cost"
            " accounting and expensed intangibles understate true equity"
            " for asset-light firms, so it says little about software"
            " companies. None when book equity is not positive. The most"
            " meaningful multiple for banks and insurers."
        ),
    )
    price_to_sales: float | None = Field(
        default=None,
        description=(
            "Market capitalization / trailing revenue. Below 1 cheap per"
            " revenue dollar (or a low-margin business); ~1-2 typical for a"
            " mature company; above 10 demands exceptional growth plus high"
            " margins. Must be read jointly with net margin — a high-margin"
            " and a zero-margin firm at the same multiple are not equally"
            " valued. Not for financials."
        ),
    )
    enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization: float | None = Field(
        default=None,
        description=(
            "Enterprise value / EBITDA — the standard operating multiple"
            " across capital structures. Broad market typically ~8-12;"
            " below 6 cheap (or the market is pricing decline); above 15"
            " rich or growth-priced for a mature firm. Ignores capital"
            " spending, so it flatters capital-intensive firms —"
            " cross-check the operating-income form. None when EBITDA is"
            " not positive — fall back to enterprise value to sales. Never"
            " for financials."
        ),
    )
    enterprise_value_to_earnings_before_interest_and_taxes: float | None = Field(
        default=None,
        description=(
            "Enterprise value / operating income. Typically ~10-14; below"
            " 10 (its inverse above 0.10) is classic Greenblatt-cheap"
            " territory. Charges for depreciation, so prefer it over the"
            " EBITDA form when comparing firms of different capital"
            " intensity. Not for financials."
        ),
    )
    enterprise_value_to_sales: float | None = Field(
        default=None,
        description=(
            "Enterprise value / trailing revenue — the leverage-corrected"
            " price-to-sales, and the fallback when EBITDA is negative."
            " Roughly 1-3 typical; above 10 unusual (requires exceptional"
            " growth and margins). Margin context is mandatory. Not for"
            " financials."
        ),
    )
    free_cash_flow_yield: float | None = Field(
        default=None,
        description=(
            "Free cash flow / market capitalization, as a decimal fraction."
            " Above 0.08 value territory (or the market doubts the cash"
            " flow's durability); 0.04-0.08 reasonable; below 0.02"
            " expensive or a heavy-reinvestment phase — check capital"
            " expenditure intensity before calling it overvalued. A wide"
            " gap versus earnings yield is itself an accrual-quality flag."
            " Compare against the 10-year Treasury yield. Meaningless for"
            " banks; REITs use an adjusted-funds-from-operations yield."
        ),
    )
    dividend_yield: float | None = Field(
        default=None,
        description=(
            "Trailing common dividends paid / market capitalization, as a"
            " decimal fraction. Roughly 0.02-0.04 typical for dividend"
            " payers; above 0.06-0.08 usually means the market is pricing a"
            " cut (value-trap territory). Zero is uninformative for"
            " no-dividend growth companies. Read as a pair with the payout"
            " ratio."
        ),
    )
    payout_ratio: float | None = Field(
        default=None,
        description=(
            "Dividends paid / net income, as a decimal fraction. 0.30-0.60"
            " is the sustainable sweet spot for a mature payer; above 1 (or"
            " above free cash flow) is unsustainable; very low at a mature"
            " firm signals capacity to raise. None when net income is not"
            " positive — compare dividends against free cash flow instead."
            " REITs structurally run at or above 0.90 (required"
            " distributions), measured against funds from operations."
        ),
    )
    shareholder_yield: float | None = Field(
        default=None,
        description=(
            "(Dividends + buybacks - stock issuance) / market"
            " capitalization, as a decimal fraction. Roughly 0.02-0.05"
            " typical for a capital-returning firm; above 0.05 aggressive"
            " capital return; negative means a net issuer — a documented"
            " negative signal. Net of issuance by design, so buybacks that"
            " merely offset stock-compensation dilution don't count."
        ),
    )

    # ------------------------------------------------------------------
    # Composite scores
    # ------------------------------------------------------------------

    piotroski_f_score: FScoreResult | None = Field(
        default=None,
        description=(
            "Piotroski (2000) nine-signal score with per-signal detail."
            " 8-9 strong, 3-7 middling (no signal either way), 0-2 weak; 7+"
            " is the common long-screen cutoff. Compare score against"
            " max_score — 5 of 6 evaluable signals reads differently from 5"
            " of 9. Designed for cheap (high book-to-market) non-financial"
            " stocks; exclude financials."
        ),
    )
    altman_z_score: float | None = Field(
        default=None,
        description=(
            "Altman (1968) bankruptcy-distress score, original model — for"
            " public manufacturers only. Above 2.99 safe; 1.81-2.99 grey"
            " zone; below 1.81 distress. Never apply to financials"
            " (leverage is their business model); use the double-prime"
            " variant for other non-manufacturers."
        ),
    )
    altman_z_zone: str | None = Field(
        default=None,
        description=(
            "Zone label for altman_z_score: 'safe' (> 2.99), 'grey', or"
            " 'distress' (< 1.81)."
        ),
    )
    altman_z_double_prime: float | None = Field(
        default=None,
        description=(
            "Altman Z'' variant for non-manufacturers (book equity in the"
            " fourth term, asset turnover dropped). Above 2.6 safe; 1.1-2.6"
            " grey zone; below 1.1 distress. Never apply to financials."
        ),
    )
    altman_z_double_prime_zone: str | None = Field(
        default=None,
        description=(
            "Zone label for altman_z_double_prime: 'safe' (> 2.6), 'grey',"
            " or 'distress' (< 1.1)."
        ),
    )
    dupont_three_factor: DuPontThreeFactor | None = Field(
        default=None,
        description=(
            "Return on equity decomposed as net margin x asset turnover x"
            " equity multiplier. High return on equity earned from margin"
            " or turnover is operationally earned (higher quality); driven"
            " mainly by the equity multiplier, it is leverage-manufactured"
            " (fragile). Bank equity multipliers are structurally huge —"
            " compare within sector."
        ),
    )
    dupont_five_factor: DuPontFiveFactor | None = Field(
        default=None,
        description=(
            "Return on equity decomposed as tax burden x interest burden x"
            " operating margin x asset turnover x equity multiplier —"
            " separates operating performance from financing and tax"
            " effects. None when pretax income or operating income is not"
            " positive (terms uninterpretable)."
        ),
    )
    beneish_m_score: BeneishResult | None = Field(
        default=None,
        description=(
            "Beneish (1999) earnings-manipulation score with its eight"
            " component indices. An m_score above -1.78 flags a likely"
            " manipulator (-2.22 is the conservative cutoff) — a red flag"
            " to investigate, never a rating to maximize; the accruals term"
            " dominates. Never score financials."
        ),
    )
