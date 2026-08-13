# Calculation Notes: `metrics.py`

Implementation notes for the metric-calculation module. This documents *how* the
metrics from [fundamental_metrics.md](fundamental_metrics.md) are implemented; that
document remains the authority on *what* each metric means, its formula, and its
sourcing.

---

## 1. What was built

- **`metrics.py`** (repo root) — pure calculation functions for every metric in the
  reference doc: all seven pillars plus the four composite scores. One function per
  metric, plus shared building blocks.
- **`tests/test_metrics.py`** — 23 tests covering every function against
  hand-computed expected values.
- **`pyproject.toml`** — added `pytest` as a dev dependency and pytest configuration
  (`pythonpath = ["."]` so the flat repo layout imports during collection,
  `testpaths = ["tests"]`).

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
  (365-day year via the `DAYS_PER_YEAR` constant).
- **Flow inputs must cover the same period** (typically TTM); balance-sheet inputs
  are point-in-time. Where the CFA convention calls for an average balance the
  parameter is named `average_...` — use the `average(beginning, ending)` helper. The
  module does not compute TTM; that is the data layer's job (reference doc §11,
  pitfall 3).

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

`tests/test_metrics.py` checks every function against hand-computed values from one
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
EDGAR companyfacts ──▶ tag-mapping / fallback chains ──▶ named inputs ──▶ metrics.py
                       (reference doc §11)                (revenue, operating_cash_flow, ...)
stock_directory.json ──▶ market_capitalization ─────────────────┘
```

The data layer resolves each named input per company (handling tag fallbacks, TTM,
Q4 differencing, restatement dedup, and financial-sector detection), then calls
these functions. Gaps arrive as `None` and propagate to `None` results; the
reporting layer renders those as "n/a" with the reference doc's sector flags
explaining why.
