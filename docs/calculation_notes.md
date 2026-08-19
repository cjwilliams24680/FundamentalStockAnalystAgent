# Calculation Notes: `calculations.py`

Implementation notes for the metric-calculation module. This documents *how* the
metrics from [fundamental_metrics.md](fundamental_metrics.md) are implemented; that
document remains the authority on *what* each metric means, its formula, and its
sourcing.

---

## 1. What was built

- **`calculations.py`** (`src/stock_analyst/analysis/`) — pure calculation functions for every
  metric in the reference doc: all seven pillars plus the four composite scores. One function
  per metric, plus shared building blocks.
- **`tests/test_calculations.py`** — 23 tests covering every function against
  hand-computed expected values.
- **`pyproject.toml`** — added `pytest` as a dev dependency and pytest configuration
  (`testpaths = ["tests"]`; the src layout imports via the editable install).

Run the tests with:

```sh
uv run pytest
```

---

## 2. Design decisions

### Pure functions, decoupled from data sourcing

Every function takes plain numbers (`float | None`) and returns a result — nothing in
the module fetches data, reads files, or knows about SEC EDGAR. This was deliberate:

- The future XBRL data layer (with its tag fallback chains, TTM derivation, and Q4
  differencing — see §11 of the reference doc) can be built and changed independently.
- Every function is trivially testable with literal numbers.
- The same functions work regardless of data source (EDGAR API, bulk files, or manual
  input).

The wiring contract is simple: the data layer's job is to produce the named inputs
(`revenue`, `operating_cash_flow`, `average_total_assets`, ...); this module's job
is everything after.

### `None` is a first-class result, not an error

Every input is typed `float | None` and every function returns `None` in three cases:

1. **Missing input** — any required argument is `None`. Real XBRL data has gaps
   (see the reliability ranking in the reference doc §11), so gaps flow through
   calculations without callers wrapping every call in checks.
2. **Zero denominator** — never raises `ZeroDivisionError`.
3. **Not meaningful** — cases the reference doc explicitly calls undefined or
   misleading return `None` rather than a nonsense number:

   | Function | Returns `None` when | Doc rationale |
   |---|---|---|
   | `price_to_earnings` | net income ≤ 0 | price-to-earnings undefined on losses — rank on `earnings_yield` instead |
   | `price_to_book` | book equity ≤ 0 | negative book value |
   | `debt_to_equity`, `return_on_equity`, `financial_leverage` | equity ≤ 0 | meaningless with negative equity — fall back to `debt_to_capital` / return on invested capital |
   | `interest_coverage` (and the EBITDA-based variant) | interest expense ≤ 0 | "no debt" is not infinite coverage — report not-meaningful |
   | `net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization`, `enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization`, `free_cash_flow_conversion` | EBITDA ≤ 0 | ratio meaningless; fall back to sales multiples |
   | `operating_cash_flow_to_net_income`, `payout_ratio` | net income ≤ 0 | ratio explodes near zero — use `sloan_accruals_ratio` / compare dividends to free cash flow |
   | `growth_rate`, `compound_annual_growth_rate` | base period ≤ 0 | growth off a non-positive base is meaningless |
   | `working_capital_turnover` | average working capital ≤ 0 | CFA: uninterpretable there |
   | `effective_tax_rate`, `reinvestment_rate`, `dupont_five_factor` | pretax income / after-tax operating profit / operating income ≤ 0 | components uninterpretable |

   One deliberate asymmetry: net debt over EBITDA **does** return negative values
   (net cash — meaningful), while enterprise value over EBITDA and
   `price_to_earnings` do not (negative multiples are not).

### No abbreviations in identifiers

Function names, parameters, variables, dataclass fields, and dictionary keys spell
terms out in full: `operating_cash_flow` not `cfo`, `capital_expenditures` not
`capex`, `cost_of_goods_sold` not `cogs`, `compound_annual_growth_rate` not `cagr`,
`average_...` not `avg_...`, `market_capitalization` not `market_cap`, and even
`earnings_before_interest_taxes_depreciation_and_amortization` rather than
`ebitda`. Proper names stay as names (Piotroski F-Score, Altman Z, Beneish M,
Sloan, DuPont). Docstrings note the common short form (for example, "commonly
abbreviated EBITDA") so functions can be matched to the terminology in the
reference doc. New code in this repo should follow the same rule.

### Sign and unit conventions

- **Monetary inputs are absolute amounts** in the filing's currency, not per-share
  (`earnings_per_share` exists to derive per-share values when needed).
- **Capital expenditures, dividends, buybacks, and stock issuance are positive
  magnitudes** — cash flow statement outflows/inflows with the sign stripped.
  Exception: `sloan_accruals_ratio` takes `investing_cash_flow` with its natural
  statement sign (usually negative), matching the published formula.
- **Ratios return decimal fractions** (0.25 = 25%); day-count metrics return days
  (365-day year via the `_DAYS_PER_YEAR` constant).
- **Flow inputs must cover the same period** (typically TTM); balance-sheet inputs
  are point-in-time. Where the CFA convention calls for an average balance the
  parameter is named `average_...` — use the `average(beginning, ending)` helper. The
  module does not compute TTM; that is the data layer's job (reference doc §11,
  pitfall 3).

### Unit scaling and year-to-date annualization

Two deterministic transformations sit between the parsing agent and `calculations.py`,
both implemented as pure methods on `RawQuantitativeData` (they exist
because the first NVDA run produced a price-to-sales of ~66 million: parsed
values printed "in millions" were divided into a whole-dollar market cap).

**Unit scaling** (`apply_unit_scale`). Filings print statement amounts at a
stated scale — a caption near the table title such as "(In millions, except per
share data)". The parsing agent records numbers *exactly as printed* (its prompt
forbids converting), the table-extraction agent captures the caption as a
structured enum (`table_parser.FinancialStatementUnitScale`: units / thousands /
millions / billions), and `quantitative_data_parser._parse_quantitative_values_from_table`
multiplies each table's parse result by the enum's factor before results are merged — per table,
because different tables can state different scales. Python does the
multiplication so the LLM never writes 12-digit numbers. For the caption to be
visible to the extraction agent, `pdf_reader.load_pdf_with_markdown_tables`
groups each PDF page's markdown tables *and* its extracted text into one string
(it previously returned them as separate list entries, so the agent saw a bare
table with the caption stranded in a different chunk and had to guess the
scale). Share counts follow the
caption's wording: "except per share data" means share counts share the stated
scale (the common large-filer convention); "except share and per share data"
means they are raw, and the extraction agent records that as
`share_counts_reported_in_stated_scale = false` so `weighted_average_diluted_shares`
is left unscaled.

**Annualization** (`annualize_year_to_date_flow_values`). Flow values are
fiscal-year-to-date (the only period a 10-Q's cash flow statement provides), but
the reference bands in `calculated_values.py` assume annual flows — a Q1 filing's
price-to-earnings would read 4× too high. `run_all_calculations` therefore
multiplies every flow field by 4 / quarter number before computing any metric:

| Fiscal quarter | Year-to-date coverage | Factor |
| --- | --- | --- |
| Q1 | 3 months | 4 |
| Q2 | 6 months | 2 |
| Q3 | 9 months | 4/3 |
| Q4 | 12 months | 1 |

The factor is uniform across all flows, so flow/flow metrics (margins, coverage,
payout, cash-flow-to-net-income) are invariant, while flow-vs-stock and
flow-vs-market-cap metrics become run-rate annual. Balance-sheet fields and
`weighted_average_diluted_shares` (a period average, not a cumulative flow) are
untouched. The module-level frozensets in `quantitative_data.py`
classify every field, and a test asserts they partition the model exactly, so a
new field cannot be added without deciding its bucket.

Known limitations (documented, not fixed):

- A statement that continues onto a page whose text lacks the scale caption
  leaves the extraction agent guessing for that continuation table; it may fall
  back to `units` and leave those values silently unscaled. A magnitude sanity
  check (e.g. total assets vs. market cap) would catch this and is a candidate
  follow-up.
- `end_of_financial_period_parser.get_earnings_period_info` maps calendar month → fiscal
  quarter assuming quarter-ends near calendar quarters; an off-cycle fiscal year
  (e.g. ending June 30) misidentifies the quarter — a pre-existing issue the
  annualization factor inherits. The robust fix is deriving the quarter from the
  "Three/Six/Nine months ended" column label.
- Annualization assumes a flat run rate; seasonal businesses look distorted
  early in their fiscal year. The affected `calculated_values.py` field
  comments carry a run-rate caveat so interpretation agents read them
  accordingly.

### Shared building blocks

Composed quantities are defined once and reused, so a convention decision lives in
exactly one place:

- `total_debt` — Damodaran's definition: interest-bearing short- + long-term debt
  plus leases, **never** total liabilities.
- `net_debt` — total debt − cash − marketable securities.
- `invested_capital` — debt + equity − cash (cash netted out because interest income
  is not operating income).
- `enterprise_value` — market capitalization + debt (+ preferred + minority
  interest, both defaulting to 0) − cash. Market capitalization comes from
  `data/stock_directory.json`; no share-price feed is needed anywhere in the module.
- `earnings_before_interest_taxes_depreciation_and_amortization` — operating income
  + depreciation and amortization, with the latter taken from the cash flow
  statement (income-statement depreciation is often buried in cost of goods sold
  or overhead lines).
- `net_operating_profit_after_tax` — operating income × (1 − effective tax *rate*),
  never actual taxes paid (that would double-count the debt tax shield).
- `free_cash_flow` — operating cash flow − capital expenditures, the app-standard
  form from the reference doc.

### Composite scores return dataclasses, not bare numbers

Frozen dataclasses (matching the `StockInfo` idiom in `stock_directory.py`) carry the
detail that makes a composite interpretable:

- **`piotroski_f_score` → `FScoreResult`** — `score`, `max_score`, and a per-signal
  dict of `True` / `False` / `None` (not evaluable). `max_score` counts only
  evaluable signals, so with partial data a 5/6 reads differently from a misleading
  5/9. Only an explicit `common_stock_issued <= 0` earns the no-issuance point — an
  unknown (`None`) does not.
- **`altman_z_score`** returns the raw Z; separate `altman_z_zone` /
  `altman_z_double_prime_zone` classifiers map to `"safe"` / `"grey"` / `"distress"`
  because the two model variants have different thresholds. The caller picks the
  variant: original for manufacturers (SIC 2000–3999), Z″ for other non-financials.
- **`dupont_three_factor` / `dupont_five_factor` → `DuPontThreeFactor` /
  `DuPontFiveFactor`** — the components, with `.return_on_equity` as a derived
  property so the decomposition always multiplies back to the directly computed
  ratio exactly (asserted in tests against `return_on_equity`).
- **`beneish_m_score` → `BeneishResult`** — the M-score, all eight indices (keyed by
  their full names, e.g. `days_sales_in_receivables_index`), and a
  `likely_manipulator` property using the original paper's −1.78 threshold. Inputs
  are two `BeneishPeriod` dataclasses (current and prior year) rather than ~24 loose
  arguments. Uses the original paper's 4.679 total-accruals coefficient, not the
  4.697 that circulates in secondary sources.

### Quarterly-report computability audit

Every function was audited against the rule that the app computes metrics from
quarterly earnings reports (10-Q filings, with the 10-K serving as the Q4/annual
filing): each parameter must be a line item on the income statement, balance
sheet, or cash flow statement in those filings — or derivable from two
consecutive filings (averages, working-capital changes, trailing-twelve-month
sums) — with one allowed exception: `market_capitalization`, which comes from
`data/stock_directory.json` rather than filings (a confirmed scope decision, so
the valuation metrics and the original Altman Z-Score stay).

Two metrics failed the audit and were removed:

- **Return on net operating assets (RNOA, Penman)** — "net operating assets" and
  "after-tax operating income" are not line items; producing them requires
  reformulating the statements into operating vs financing components, which is
  analyst judgment rather than scraping. Return on invested capital is the
  practical stand-in.
- **Fixed-charge coverage** — lease *payments* appear in lease footnotes, not the
  three statements; without the lease terms the formula collapses into plain
  `interest_coverage`, which already exists.

### What is deliberately *not* in the module

- **PEG** — excluded per the reference doc (§8): the canonical form needs analyst
  forecasts the app doesn't have, and the historical-growth impostor misleads.
- **Sector gating** — deciding that a bank shouldn't get a current ratio is
  app-layer logic (detect via SIC code / directory sector and *don't call* the
  function). The functions themselves are sector-agnostic; the reference doc's
  summary table says which metrics to suppress where.
- **TTM computation, XBRL tag mapping, Q4 derivation** — data-layer concerns
  (reference doc §11).
- **FFO/AFFO for REITs** — deferred along with the other sector-specific metric
  sets, per the project's scope decision.

---

## 3. Testing approach

`tests/test_calculations.py` checks every function against hand-computed values from one
coherent fake company (stated in the test module docstring: revenue 1000, COGS 600,
net income 120, operating cash flow 300, capital expenditures 80, total assets
2000, equity 1000, market capitalization 5000, ...), so cross-metric identities
hold — e.g., DuPont components multiply back to the directly computed return on
equity.

Beyond the happy path, the tests pin the edge-case semantics:

- Each "not meaningful → `None`" rule in the table above has an explicit assertion.
- **F-Score**: an all-signals-pass year scores 9/9; nulling two inputs drops
  `max_score` to 7 while the score stays consistent; a losing, stock-issuing year
  fails exactly the expected signals (and still earns CFO > net income).
- **Z-Score**: both variants verified against hand-worked arithmetic
  (Z = 4.33, Z″ = 3.357) plus all three zone boundaries.
- **Beneish**: identical periods drive all seven indices to exactly 1.0 and the
  score to its analytic value (not flagged); a ballooning-receivables /
  negative-cash-flow year trips `likely_manipulator`; an uncomputable index
  (zero prior revenue) returns `None` rather than a partial score.

---

## 4. How the next phase plugs in

The intended flow once the EDGAR layer exists:

```
EDGAR companyfacts ──▶ tag-mapping / fallback chains ──▶ named inputs ──▶ calculations.py
                       (reference doc §11)                (revenue, operating_cash_flow, ...)
stock_directory.json ──▶ market_capitalization ─────────────────┘
```

The data layer resolves each named input per company (handling tag fallbacks, TTM,
Q4 differencing, restatement dedup, and financial-sector detection), then calls
these functions. Gaps arrive as `None` and propagate to `None` results; the
reporting layer renders those as "n/a" with the reference doc's sector flags
explaining why.
