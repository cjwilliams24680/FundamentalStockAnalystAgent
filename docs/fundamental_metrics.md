# Fundamental Analysis Metrics Reference

A curated, sourced list of the values and ratios experts consider most important for
fundamental stock analysis, selected for computability from SEC 10-Q/10-K filing data
plus the market capitalization already stored in `data/stock_directory.json`.

---

## 1. Introduction

**Fundamental analysis** evaluates a company's intrinsic worth from its financial
statements — the income statement, balance sheet, and cash flow statement filed with the
SEC — rather than from price charts or market sentiment. The core questions it answers:

- Is the business **profitable**, and are those profits high-quality?
- Can it **pay its bills** next quarter (liquidity) and survive its debt load (solvency)?
- How **efficiently** does it turn assets into sales?
- Does reported profit turn into actual **cash**?
- Is it **growing**, and is that growth worth anything?
- Is the stock **cheap or expensive** relative to those fundamentals?

This document organizes the consensus metrics into those **seven pillars** —
profitability, efficiency, liquidity, solvency/leverage, cash flow, growth, and
valuation — plus a section on **composite scores** that combine base metrics into a
single number.

### How to read this document

Each metric carries:

- **Tier** — `CORE` (a metric analysts always check; ~20 in total) or `EXTENDED`
  (adds depth, or serves a specific situation such as distress screening).
- **Formula** — with the exact convention (e.g., average vs ending balance-sheet values;
  which definition of "debt"). Balance-sheet denominators use the **average** of
  beginning and ending values per CFA Institute convention unless noted.
- **Inputs** — which financial statement each input comes from: income statement (IS),
  balance sheet (BS), cash flow statement (CF), or market data (market cap).
- **Interpretation** — what good looks like, thresholds where authoritative sources give
  them, and common pitfalls. Golden rule (CFA Institute): almost all ratios are only
  meaningful **relative to industry peers and to the company's own history** — absolute
  "good ranges" are the exception, not the rule.
- **Reference values** — where the interpretation prose lacks explicit numbers, a
  `Reference values:` line gives rough practitioner bands for what reads as good, bad,
  or unusual. These are heuristics for flagging, not verdicts: they are subordinate to
  the golden rule above and to the sector notes, and "unusual" means *verify the inputs
  and context* — not automatically bad.
- **Sector notes** — where the metric breaks down. Two flags recur:
  - 🏦 **Financials (banks, insurers, brokers)** — file *unclassified* balance sheets
    (no current/non-current split), treat debt as raw material rather than financing,
    and book interest as an operating cost. This invalidates current/quick ratios, all
    EBITDA- and EV-based metrics, ROIC, turnover ratios, and FCF metrics. What still
    works: ROE, ROA, net margin, P/E, P/B, EPS growth, DuPont.
  - 🏢 **REITs** — GAAP depreciation on property overstates economic depreciation, so
    net income, EPS, and P/E understate REIT earnings power. The industry-standard
    substitutes are FFO/AFFO (Nareit definitions). REITs also structurally run high
    leverage and high payout ratios (they must distribute ≥90% of taxable income).
- **Data difficulty** — Easy / Medium / Hard, reflecting how reliably the inputs are
  tagged in SEC XBRL data (see [Implementation notes](#10-implementation-notes-sec-edgar-data)).
- **Sources** — the authoritative sources supporting inclusion, by tier:
  **T1** = CFA Institute curriculum/readings; **T2** = academic & practitioner canon
  (Damodaran, McKinsey, Penman, Graham, original papers); **T3** = professional
  platform/screener practice; **T4** = reference sites, used for cross-checking only.
  Full citations in the [Bibliography](#11-bibliography).

### How this list was selected

Candidates were gathered from T1–T3 sources per pillar, then filtered on three criteria:
(1) **expert consensus** — supported by at least two independent T1–T3 sources;
(2) **computability** — every input obtainable from 10-Q/10-K data, or filing data plus
market cap (metrics requiring share-price history or analyst estimates are excluded or
flagged, e.g., PEG); (3) **pillar coverage** — the final set spans all seven pillars.
Near-duplicate metrics were tiered rather than all promoted (e.g., current ratio CORE,
cash ratio EXTENDED), and each metric was checked against the SEC XBRL `us-gaap`
taxonomy for how reliably its inputs are actually tagged by filers.

---

## 2. Profitability

How much profit the company squeezes from its revenue and its capital. Two families:
**margins** (profit ÷ revenue, the "margin waterfall") and **returns on capital**
(profit ÷ the money invested to earn it).

### Gross Profit Margin — CORE

- **Formula:** Gross Profit ÷ Revenue, where Gross Profit = Revenue − Cost of Goods Sold.
- **Inputs:** Revenue (IS), COGS (IS).
- **Interpretation:** The share of each revenue dollar left after direct product costs — a
  proxy for pricing power and product differentiation. Trend matters more than level:
  an eroding gross margin is an early warning that competition or input costs are biting.
  Cross-industry comparison is nearly meaningless (software runs 70–90%, retail 20–40%);
  compare only against peers and history.
- **Reference values:** The sector ranges above are the anchor; a negative gross
  margin — selling below direct cost — is a severe flag at any scale.
- **Sector notes:** 🏦 Undefined for financials (no COGS line). 🏢 Largely unused for REITs.
- **Data difficulty:** Hard — many filers don't tag `GrossProfit` (~43% direct); derive as
  Revenue − CostOfRevenue, with COGS tags split across current and deprecated concepts.
- **Sources:** CFA Institute Financial Ratio List #15 (T1); CFA Financial Analysis
  Techniques (T1); also the numerator of Piotroski's F_ΔMARGIN signal (T2).

### Operating Profit Margin — CORE

- **Formula:** Operating Income ÷ Revenue.
- **Inputs:** Operating income (IS), Revenue (IS).
- **Interpretation:** Profitability after *all* operating costs but before financing and
  taxes — the cleanest measure of the underlying business's economics, comparable across
  capital structures. CFA guidance: operating margin improving faster than gross margin
  signals better overhead control. Pitfall: companies vary in what they classify as
  "operating" (one-off charges, stock compensation).
- **Reference values:** Negative = the operations themselves lose money. <5% thin;
  roughly 10–20% healthy for most industries; >20% strong (the large-cap US median
  runs in the low-to-mid teens); >40% unusual — verify what the filer classifies as
  operating costs.
- **Sector notes:** 🏦 Not meaningful — interest is a bank's operating cost, so the EBIT
  concept breaks down (banks are judged on the "efficiency ratio" instead).
- **Data difficulty:** Easy — `OperatingIncomeLoss` is tagged by ~83% of filers (banks
  account for much of the gap, which is correct behavior).
- **Sources:** CFA Ratio List #16 (T1); Damodaran, *Valuing Financial Service Firms*
  for the financials exclusion (T2).

### Net Profit Margin — CORE

- **Formula:** Net Income ÷ Revenue.
- **Inputs:** Net income (IS), Revenue (IS).
- **Interpretation:** Bottom-line conversion of revenue into profit for shareholders.
  Completes the margin waterfall (gross → operating → net); comparing the three across
  time shows *where* profitability is won or lost. Pitfall: polluted by one-off gains
  and losses and tax-rate swings — check the pretax margin and tax rate when net margin
  jumps.
- **Reference values:** Negative = net loss. <5% thin; 5–10% about average; 10–20%
  good; >20% excellent; >30% unusual — check for one-off gains or tax items before
  crediting the underlying business.
- **Sector notes:** Works for financials (needs no operating/financing split).
  🏢 Depressed for REITs by property depreciation; FFO-based margins are the substitute.
- **Data difficulty:** Easy for the numerator (`NetIncomeLoss` ~99%); Medium overall
  because Revenue needs a tag-fallback chain (see implementation notes).
- **Sources:** CFA Ratio List #18 (T1); universal across T3 platforms.

### Return on Equity (ROE) — CORE

- **Formula:** Net Income ÷ **Average** Shareholders' Equity. Refinement: use net income
  minus preferred dividends over average *common* equity.
- **Inputs:** Net income (IS), shareholders' equity (BS, two period-ends).
- **Interpretation:** The return the company earns on its owners' capital — the single
  most-cited profitability metric. A sustained ~15%+ is the common quality bar in
  screener practice; compare against the cost of equity. **Never read ROE alone**: it is
  mechanically inflated by leverage, which is exactly what the DuPont decomposition
  (§9) untangles. Pitfalls: meaningless when book equity is negative (common after
  heavy buybacks — fall back to ROIC); flattered by write-downs that shrink the
  denominator.
- **Sector notes:** 🏦 **The** primary metric for banks and insurers — Damodaran shows
  the ROE↔P/B relationship is the strongest valuation link for financials.
  🏢 Distorted for REITs (depreciated book values).
- **Data difficulty:** Easy — both inputs near-universally tagged.
- **Sources:** CFA Ratio List #21/#24 (T1); Damodaran, *Return Measures* paper (T2);
  Penman (T2).

### Return on Invested Capital (ROIC) — CORE

- **Formula:** NOPAT ÷ Average Invested Capital, where **NOPAT = EBIT × (1 − effective
  tax rate)** and **Invested Capital = interest-bearing debt + shareholders' equity −
  cash** (equivalently: fixed assets + non-cash working capital). Use the effective tax
  *rate*, never actual taxes paid (that double-counts the debt tax shield — Damodaran).
- **Inputs:** EBIT and tax rate (IS); debt, equity, cash (BS).
- **Interpretation:** The value-creation metric modern practice treats as primary for
  non-financial companies: **growth only creates value when ROIC exceeds the cost of
  capital** — the organizing principle of McKinsey's *Valuation* and Damodaran's
  framework. Unlike ROE it can't be juiced with leverage. Pitfalls: book capital embeds
  old accounting choices (past write-offs inflate ROIC); judge the *trend* and the
  spread over WACC, not the raw level.
- **Reference values:** Anchor to the cost of capital: typical large-cap WACC is
  ~8–10%, so ROIC <8% is likely value-destroying, 10–15% solid, >15% strong (durable
  competitive-advantage territory), and >40% unusual — usually book capital shrunken
  by past write-offs rather than superhuman economics.
- **Sector notes:** 🏦 Undefined for financials (debt is their raw material, so "invested
  capital" and EBIT don't exist in the corporate sense — use ROE). 🏢 Distorted for
  REITs by property book values.
- **Data difficulty:** Medium — EBIT and equity are easy; the debt component requires a
  multi-tag fallback chain with double-count risk (see implementation notes).
- **Sources:** CFA Ratio List #22–23 (T1); Damodaran, *Return Measures* (T2);
  McKinsey *Valuation* / growth-vs-ROIC research (T2).

### EBITDA Margin — EXTENDED

- **Formula:** EBITDA ÷ Revenue, where EBITDA = Operating Income + Depreciation &
  Amortization (take D&A from the cash flow statement — income-statement D&A is often
  buried in COGS/SG&A).
- **Inputs:** Operating income (IS), D&A (CF), Revenue (IS).
- **Interpretation:** A capital-structure- and depreciation-policy-neutral margin,
  dominant in credit analysis and EV/EBITDA comps — which is why it's here. But treat
  it as a comps convenience, not a quality signal: depreciation is a real cost
  (Buffett's critique), and Moody's *Putting EBITDA Into Perspective* catalogs ten
  failings. A 35% EBITDA margin at a telecom is not a 35% margin at a software firm.
- **Reference values:** Rough sector bands: >30–40% software/pharma/infrastructure;
  15–25% typical industrials; <10% thin (though normal in distribution and retail);
  negative = severe — the business isn't covering even its cash operating costs.
- **Sector notes:** 🏦 Explicitly rejected for financials. 🏢 REITs use EBITDAre
  (Nareit-standardized variant).
- **Data difficulty:** Medium — D&A tagging is split across three tag families.
- **Sources:** Moody's special comment (T3); Damodaran (T2); standard on all platforms (T3).

### Return on Assets (ROA) — EXTENDED

- **Formula:** Net Income ÷ Average Total Assets.
- **Inputs:** Net income (IS), total assets (BS, two period-ends).
- **Interpretation:** Return per dollar of assets regardless of financing. For general
  use it's dominated by ROIC (its numerator belongs to equity holders while its
  denominator is funded by everyone — an inconsistency both CFA materials and Damodaran
  flag). Kept because it is a **bank staple**: return on average assets ~1%+ is the
  classic good-bank threshold, and it's the profitability input to Piotroski's F-Score.
- **Reference values:** For non-financials, >5% is good and >10% excellent. Banks run
  on a different scale entirely — return on average assets ~1%+ is the good-bank bar.
- **Sector notes:** 🏦 One of the few return metrics that *works* for banks.
- **Data difficulty:** Easy.
- **Sources:** CFA Ratio List #19–20 (T1); Damodaran, *Return Measures* (T2, critically);
  Piotroski 2000 (T2).

> **Removed in the quarterly-report audit:** Return on Net Operating Assets (RNOA,
> Penman) — its inputs require reformulating the statements into operating vs
> financing components, which is analyst judgment rather than something scrapable
> from a quarterly filing. ROIC is the practical stand-in.

---

## 3. Efficiency

How hard the asset base works: revenue per dollar of assets, and how fast inventory,
receivables, and payables turn over.

### Total Asset Turnover — CORE

- **Formula:** Revenue ÷ Average Total Assets.
- **Inputs:** Revenue (IS), total assets (BS, two period-ends).
- **Interpretation:** Revenue generated per dollar of assets (1.5 = $1.50 per $1). The
  bridge in the DuPont identity: profitability = margin × turnover, and businesses
  strategically trade one for the other (luxury = high margin/low turnover, discount
  retail = the reverse). A low value can just mean capital intensity, not
  inefficiency — peer-relative only.
- **Reference values:** Most non-financials fall roughly 0.5–2.0; <0.25 outside
  utilities/real estate is unusual (idle assets or an overvalued asset base).
- **Sector notes:** 🏦 Trivially tiny for banks (~0.03–0.1) and carries no signal there.
  Low-information for asset-light software.
- **Data difficulty:** Easy (given the revenue fallback chain).
- **Sources:** CFA Ratio List #14 (T1); Penman decomposition (T2); Piotroski F_ΔTURN (T2).

### Cash Conversion Cycle (CCC) — CORE (companies with inventory)

- **Formula:** CCC = DIO + DSO − DPO, from its three day-count components:
  - **Days Inventory on Hand (DIO)** = 365 ÷ (COGS ÷ Average Inventory)
  - **Days Sales Outstanding (DSO)** = 365 ÷ (Revenue ÷ Average Receivables)
  - **Days Payables Outstanding (DPO)** = 365 ÷ (Purchases ÷ Average Payables), where
    Purchases ≈ COGS + ΔInventory (COGS alone is the accepted fallback)
- **Inputs:** COGS, Revenue (IS); inventory, receivables, payables (BS, two period-ends).
- **Interpretation:** Days of cash tied up between paying suppliers and collecting from
  customers. Lower is better; negative (suppliers finance the operation, Amazon-style)
  is a structural advantage. The *components* are the diagnostics: **rising DSO faster
  than revenue is a classic channel-stuffing / aggressive-revenue-recognition red flag;
  rising DIO flags obsolescence risk.** High DPO is ambiguous — bargaining power or
  payment distress — triangulate with liquidity ratios (CFA).
- **Reference values:** For manufacturers/retailers a CCC of roughly 30–90 days is
  common; negative is a structural advantage. Components: DSO ~30–60 days typical,
  >90 unusual (collection problems or channel stuffing); DPO ~30–60 days typical.
- **Sector notes:** 🏦🏢 Undefined for financials and REITs; degenerate for no-inventory
  businesses (software, services) — display conditionally.
- **Data difficulty:** Medium — inventory/receivables/payables tags are present for
  53–61% of filers, but absence is often legitimate (no inventory).
- **Sources:** CFA Ratio List #5–11 (T1); AnalystNotes/AnalystPrep curriculum notes (T1-derived).

### Fixed Asset Turnover — EXTENDED

- **Formula:** Revenue ÷ Average Net Fixed Assets (net PP&E).
- **Inputs:** Revenue (IS), net PP&E (BS, two period-ends).
- **Interpretation:** Efficiency of the plant/equipment base; only meaningful for
  capital-intensive sectors. Pitfall: mechanically rises as assets depreciate — an aging
  asset base looks deceptively "efficient."
- **Reference values:** Capital-intensive firms typically run ~1–4. A high or rising
  value alongside flat capital spending is the aging-asset-base artifact above —
  check capital expenditures to depreciation before crediting efficiency.
- **Sector notes:** Noise for services, software, and financials.
- **Data difficulty:** Easy.
- **Sources:** CFA Ratio List #13 (T1).

### Working Capital Turnover — EXTENDED

- **Formula:** Revenue ÷ Average Working Capital.
- **Interpretation:** CFA explicitly warns it is uninterpretable when working capital is
  near zero or negative — which is common. The CCC is the better working-capital lens.
- **Reference values:** Where defined (positive average working capital), higher =
  leaner funding of operations; >~10 is unusually high — a thin working-capital
  buffer or a structurally negative-working-capital model; cross-check the liquidity
  ratios.
- **Data difficulty:** Easy (where defined).
- **Sources:** CFA Ratio List #12 (T1).

---

## 4. Liquidity

Can the company cover its obligations over the next year without raising outside money?

### Current Ratio — CORE

- **Formula:** Current Assets ÷ Current Liabilities.
- **Inputs:** Current assets (BS), current liabilities (BS).
- **Interpretation:** ≥1 means short-term assets cover short-term obligations; Graham's
  defensive-investor standard for industrials is ≥2.0. Very high values can signal lazy
  capital. Pitfalls: inflated by slow-moving inventory and stale receivables; a
  point-in-time snapshot that can be window-dressed at period end; negative working
  capital is normal and healthy for some retail/subscription models.
- **Sector notes:** 🏦 **Meaningless for banks and insurers** — they file unclassified
  balance sheets, so the inputs literally don't exist in their filings (suppress the
  metric, don't emit garbage). 🏢 Rarely used for REITs.
- **Data difficulty:** Easy for non-financials (~80% of filers; the gap *is* the
  financials).
- **Sources:** CFA Financial Analysis Techniques (T1); Graham, *The Intelligent
  Investor* criteria (T2); Piotroski F_ΔLIQUID uses its change (T2).

### Quick Ratio (Acid-Test) — CORE

- **Formula:** (Cash + Short-term Marketable Securities + Receivables) ÷ Current
  Liabilities (CFA's additive convention).
- **Inputs:** All BS.
- **Interpretation:** ~≥1 typically healthy. Its real value is the **spread versus the
  current ratio**: a big gap flags an inventory-heavy or inventory-stuck balance sheet.
  Nearly identical to the current ratio for no-inventory businesses (redundant there).
- **Sector notes:** 🏦 Same exclusion as current ratio.
- **Data difficulty:** Medium — short-term investments are fragmented across several tags.
- **Sources:** CFA refresher (T1); AnalystPrep (T1-derived).

### Operating Cash Flow Ratio — CORE

- **Formula:** Cash Flow from Operations ÷ Current Liabilities.
- **Inputs:** CFO (CF), current liabilities (BS).
- **Interpretation:** >1 rule of thumb: operations alone cover short-term obligations.
  The strongest liquidity cross-check because it is **flow-based and much harder to
  window-dress** than balance-sheet snapshots.
- **Sector notes:** 🏦 Not meaningful (bank CFO is distorted by loan/deposit flows).
- **Data difficulty:** Easy.
- **Sources:** CFA cash-flow-ratio family (T1-derived); Wall Street Prep (T3).

### Cash Ratio — EXTENDED

- **Formula:** (Cash + Cash Equivalents + Short-term Marketable Securities) ÷ Current
  Liabilities.
- **Interpretation:** The worst-case/crisis measure. Most healthy firms run well below 1;
  useful mainly in distress screening. Cluster note: current > quick > cash — current
  is primary, quick is the cross-check, cash is the stress test.
- **Reference values:** Healthy firms typically run 0.1–0.5; >1 means current
  liabilities are fully covered by cash alone — an idle-cash hoard or a deliberate
  war chest (read with the capital-return metrics).
- **Sources:** CFA refresher (T1).

### Working Capital (level) — EXTENDED

- **Formula:** Current Assets − Current Liabilities.
- **Interpretation:** Absolute dollars, so not comparable across companies — kept as an
  input/context figure and for Graham's solvency screen: **long-term debt ≤ working
  capital**. Also X1 of the Altman Z-Score.
- **Sources:** Graham (T2); Altman 1968 (T2).

### Defensive Interval Ratio — EXTENDED

- **Formula:** (Cash + ST Securities + Receivables) ÷ Daily Cash Operating Expenses,
  where the denominator = (operating expenses − non-cash charges) ÷ 365.
- **Interpretation:** Days the firm can operate on liquid assets with zero revenue. In
  the CFA liquidity set but rarely screened on in practice.
- **Reference values:** >90 days comfortable; 30–90 adequate; <30 days tight — the
  firm depends on near-term revenue or financing to keep operating.
- **Sources:** CFA refresher (T1).

---

## 5. Solvency & Leverage

Can the company survive its debt load through a bad year — and how much of the balance
sheet is borrowed?

**Debt definition (Damodaran's rule, used throughout):** debt = all interest-bearing
liabilities, short- and long-term, plus lease obligations — **never** total liabilities.
**Net debt** subtracts cash and marketable securities.

### Debt-to-Equity — CORE

- **Formula:** Total Debt ÷ Total Shareholders' Equity.
- **Inputs:** Debt, equity (BS).
- **Interpretation:** The most-cited balance-sheet leverage measure. Higher = more
  financial risk; <1.0 is a common conservative screen for industrials, but sector norms
  dominate (utilities and REITs run high by design). Pitfalls: explodes or turns
  meaningless when equity is negative (buyback-heavy large-caps) — fall back to
  debt-to-capital, which is bounded; book equity distorted by write-offs.
- **Sector notes:** 🏦 Structurally high for financials (debt is raw material) — generic
  benchmarks mislead; use the equity multiplier and regulatory capital instead.
- **Data difficulty:** Hard — debt is fragmented across 8+ XBRL tags with aggregation
  overlap (double-count risk); best-effort summation required.
- **Sources:** CFA refresher solvency set (T1); Damodaran debt definition (T2).

### Net Debt / EBITDA — CORE

- **Formula:** (Total Debt − Cash − Marketable Securities) ÷ EBITDA (trailing 12 months).
- **Inputs:** Debt, cash (BS); operating income + D&A (IS/CF).
- **Interpretation:** Years of EBITDA needed to repay net debt — the lender's first
  screen and the leverage anchor in ratings methodologies. Reference points from credit
  practice: <1.5× minimal risk, 2–3× intermediate, 3–4× significant (common covenant
  ceiling), >4–5× highly leveraged. Negative = net cash (report as such). Pitfall:
  EBITDA ignores capex and working capital, and peak-cycle EBITDA flatters the ratio.
- **Sector notes:** 🏦 Meaningless for banks/insurers (EBITDA undefined). 🏢 REITs run
  5–7× on the Nareit EBITDAre variant — corporate thresholds mislead there.
- **Data difficulty:** Hard (same debt-tag fragmentation).
- **Sources:** CFA fixed-income credit reading (T1-derived); S&P/credit-practice
  thresholds (T3); CFI cross-check (T4).

### Interest Coverage — CORE

- **Formula:** EBIT (operating income) ÷ Interest Expense (gross, not net).
- **Inputs:** Both IS.
- **Interpretation:** How many times operating profit covers interest. Damodaran's
  synthetic-rating tables map it directly to credit ratings for large non-financials:
  ≥8.5× ≈ AAA, 3–4.25× ≈ A−, 1.25–1.5× ≈ B−; <1.5–2× is distress territory, >5×
  comfortable. Edge cases: negative EBIT or zero interest expense → report "not
  meaningful" / "no debt" rather than a number.
- **Sector notes:** 🏦 Not meaningful in standard form for banks (interest *is* the core
  operating expense; Damodaran keeps a separate financial-firm table). Fine for REITs
  and utilities.
- **Data difficulty:** Medium — `InterestExpense` is tagged directly by only ~56% of
  filers; needs fallbacks (including cash interest paid as a proxy).
- **Sources:** Damodaran synthetic ratings (T2); CFA refresher + credit reading (T1).

### Debt-to-Capital / Debt-to-Assets — EXTENDED

- **Formulas:** Total Debt ÷ (Total Debt + Equity); Total Debt ÷ Total Assets.
- **Interpretation:** Algebraic siblings of D/E, both bounded [0,1] so they stay
  well-behaved when equity is thin or negative — keep one as the robustness backup.
  Debt-to-capital is the form credit analysts prefer.
- **Reference values:** Debt-to-capital <0.3–0.4 conservative, 0.4–0.6 moderate,
  >0.6 aggressive for non-financials; debt-to-assets >0.5 means the asset base is
  majority debt-funded.
- **Sources:** CFA refresher (T1); CFA credit reading (T1-derived).

### Financial Leverage (Equity Multiplier) — EXTENDED

- **Formula:** Average Total Assets ÷ Average Total Equity.
- **Interpretation:** Assets supported per unit of equity; the leverage leg of DuPont.
  Captures *all* liabilities, not just interest-bearing debt.
- **Reference values:** ~2–3 is typical for non-financials; >5 is high — or a
  buyback-shrunken equity base, so check book equity before reading it as debt risk.
  Banks structurally run ~8–15, which is why generic bands don't apply to them.
- **Sector notes:** 🏦 **The leverage measure that stays meaningful for banks** — flag as
  the financial-sector fallback.
- **Data difficulty:** Easy.
- **Sources:** CFA refresher (T1).

### EBITDA/Interest Coverage — EXTENDED

- **Formula:** EBITDA ÷ Interest Expense.
- **Interpretation:** The more generous coverage variant (adds back D&A).
  EBIT/interest is primary (it's what Damodaran's rating map uses).
- **Reference values:** Runs above EBIT/interest by construction. Credit practice:
  >6× comfortable, 2–6× intermediate, <2× stressed.
- **Sources:** CFA credit reading (T1-derived).

> **Removed in the quarterly-report audit:** Fixed-charge coverage — lease
> *payments* live in lease footnotes, not the three statements, so they can't be
> scraped from a quarterly filing; without leases the formula collapses into plain
> interest coverage.

### CFO/Total Debt — EXTENDED

- **Formula:** Cash Flow from Operations ÷ Total Debt.
- **Interpretation:** Internally generated cash relative to the debt stack; a
  Moody's/S&P staple (~>40% associated with strong investment grade). Strong credit-side
  complement to the core pair.
- **Sector notes:** 🏦 Not for financials.
- **Sources:** CFA credit reading (T1-derived).

---

## 6. Cash Flow — Generation & Quality

Accrual accounting lets reported profit and actual cash diverge for years. This pillar
measures how much real cash the business throws off and whether earnings are backed by it.
**The persistent gap between net income and cash flow is the best-documented red flag in
the academic literature** (Sloan 1996).

### Free Cash Flow (FCF) — CORE

- **Formula (app standard):** **FCF = Cash Flow from Operations − Capital Expenditures.**
  Canonical valuation variants for reference: FCFF = EBIT(1−t) + D&A − Capex − ΔWorking
  Capital (cash to *all* capital providers); FCFE = CFO − Capex + Net Borrowing (cash to
  equity holders).
- **Inputs:** CFO, capex (CF).
- **Interpretation:** The cash genuinely available to capital providers after
  maintaining/growing the asset base — the foundation of intrinsic value. Positive and
  growing is good; persistent negative FCF is either growth investment or value
  destruction, and only ROIC context distinguishes them. Pitfalls: CFO−capex mixes
  growth and maintenance capex (overstates the burden for fast growers); stock-based
  compensation inflates CFO; single-year FCF is noisy — smooth over 3 years.
- **Sector notes:** 🏦 Essentially undefined for banks/insurers. 🏢 REITs: use FFO/AFFO
  (FFO = Net Income + real-estate D&A − gains on property sales; REITs disclose FFO in
  filings per the SEC-accepted Nareit definition).
- **Data difficulty:** Easy — CFO is the single best-tagged flow concept; capex ~65%
  direct with fallbacks.
- **Sources:** CFA Free Cash Flow Valuation reading (T1); Damodaran FCF primer (T2);
  Nareit FFO white paper for the REIT substitute (T3).

### FCF Margin — CORE

- **Formula:** FCF ÷ Revenue.
- **Inputs:** CFO, capex (CF); Revenue (IS).
- **Interpretation:** Cash-based profitability — the check on the accrual margin
  waterfall. >10% generally strong; software leaders >20%; manufacturing 10–15%; retail
  single digits normal. Smooth over multiple years (capex lumpiness).
- **Sector notes:** 🏦 Excluded; 🏢 AFFO margin instead.
- **Data difficulty:** Easy/Medium.
- **Sources:** CFA cash-flow performance ratios (T1-derived); screener practice (T3).

### Cash Flow to Net Income (CFO/NI) — CORE

- **Formula:** CFO ÷ Net Income. Screening sibling: **Sloan accruals ratio**
  = (Net Income − CFO − Cash from Investing) ÷ Total Assets.
- **Inputs:** CFO, CFI (CF); net income (IS); total assets (BS).
- **Interpretation:** The consensus earnings-quality check. Persistently ≥1 = earnings
  backed by cash (D&A alone should push most firms above 1); persistently <1 =
  accrual-driven earnings. Sloan (1996) documented that high-accrual firms
  systematically underperform; Sloan ratio between −10% and +10% is considered safe,
  >+25% a strong warning. Pitfalls: one bad year is noise (working-capital timing); the
  ratio explodes when net income ≈ 0 — prefer the asset-scaled Sloan form for screening.
  Piotroski's F_ACCRUAL is the binary version (CFO > NI).
- **Sector notes:** 🏦 Not meaningful; 🏢 compare FFO vs net income instead.
- **Data difficulty:** Easy.
- **Sources:** Sloan 1996, *The Accounting Review* (T2); Penman accruals research (T2);
  Piotroski 2000 (T2); CFA analog ratios (T1-derived).

### FCF Conversion — EXTENDED

- **Formula:** FCF ÷ EBITDA (variants: ÷ EBIT, ÷ Net Income).
- **Interpretation:** ≥80% strong, ~100% ideal; >100% usually a temporary
  working-capital benefit. Overlaps heavily with CFO/NI + capex intensity — kept as a
  one-number cross-check.
- **Sources:** Wall Street Prep (T3).

### Capex Intensity — EXTENDED

- **Formula:** Capex ÷ Revenue. Companions: Capex ÷ CFO; Capex ÷ D&A (>1 = growing asset
  base; <1 = possible underinvestment — a rough maintenance-capex proxy).
- **Interpretation:** Explains *why* FCF margin is what it is; separates asset-light
  (<5% of sales) from capital-intensive (>15%) businesses. Lumpy — average 3–5 years.
  High capex is only bad if the returns on it (ROIC) are poor.
- **Sources:** Damodaran reinvestment framework (T2); CFA reinvestment ratio (T1-derived).

---

## 7. Growth

Whether the business is expanding — read **jointly with ROIC**, because growth only
creates value when the return on new capital exceeds its cost (McKinsey's central
empirical finding; growth at poor returns destroys value).

### Revenue Growth — CORE

- **Formula:** (Revenue_t − Revenue_{t−1}) ÷ Revenue_{t−1}; multi-year:
  CAGR = (Rev_t / Rev_{t−n})^(1/n) − 1. Graham's smoothing: compare 3-year averages at
  the endpoints to strip cyclicality.
- **Inputs:** Revenue (IS), multiple periods.
- **Interpretation:** The top line of the whole model — every source starts here.
  McKinsey empirics: growth rates fade toward ~2–5% nominal over time regardless of
  industry, so extrapolating high growth is the classic error. Pitfalls: acquired vs
  organic growth conflated; FX effects invisible in the statements.
- **Reference values:** Negative = contraction (distinguish a cyclical dip from
  secular decline); 0–5% mature/GDP-pace; 5–15% healthy; >20% high growth; >40%
  sustained is rare — verify it isn't acquisition-driven.
- **Sector notes:** Universally applicable, including financials (revenue = net interest
  income + fees; rate cycles drive it). 🏢 Same-store/rental revenue more meaningful
  than the total for REITs.
- **Data difficulty:** Medium — the revenue tag chain, plus multi-period stitching across
  deprecated tags for history before 2018.
- **Sources:** McKinsey growth/ROIC research (T2); Damodaran, *Fundamental Determinants
  of Growth* (T2); universal in T3 practice.

### EPS Growth — CORE

- **Formula:** YoY % or CAGR of Diluted EPS, where EPS = (Net Income − Preferred
  Dividends) ÷ Weighted-Average Diluted Shares. Graham's defensive criterion: ≥ one-third
  cumulative growth over 10 years on 3-year average endpoints (~2.9%/yr).
- **Inputs:** Net income, share counts (IS).
- **Interpretation:** The canonical bottom-line growth metric. The per-share form is
  preferred over raw net-income growth because it captures buyback accretion and
  issuance dilution. Pitfalls: meaningless off negative/near-zero base years; one-offs
  distort; EPS growth driven by buybacks without operating-income growth is lower
  quality — show revenue, operating income, and EPS growth side by side to expose the
  difference.
- **Reference values:** ~10%+ sustained is strong; >25% rarely persists (growth
  fades); interpret only off a meaningfully positive base year.
- **Sector notes:** Fine for financials. 🏢 Misleading for REITs — use FFO/AFFO per-share
  growth.
- **Data difficulty:** Easy (EPS and share counts ~90%+ tagged).
- **Sources:** CFA Ratio List #38 (T1); Graham criteria (T2); Damodaran (T2 — with the
  caveat that historical growth forecasts poorly).

### Sustainable Growth Rate — EXTENDED

- **Formula:** SGR = Retention Rate × ROE, where Retention Rate = 1 − Payout Ratio.
- **Inputs:** Net income, dividends (IS/CF); equity (BS).
- **Interpretation:** The growth fundable from retained earnings without new capital — a
  reality check on reported growth: persistent growth above SGR requires external
  financing or improving ROE. Links growth, profitability, and payout in one identity.
- **Reference values:** Read as a comparison, not a level: actual growth persistently
  above SGR → expect share issuance or rising leverage to fund the gap; growth well
  below SGR with high ROE → capacity to raise dividends or buybacks.
- **Sources:** CFA Ratio List #36–37 (T1); Damodaran (T2).

### Reinvestment-Rate Growth (Fundamental Growth) — EXTENDED

- **Formula:** Expected Operating-Income Growth = Reinvestment Rate × ROIC, where
  Reinvestment Rate = (Net Capex + ΔNon-cash Working Capital) ÷ NOPAT.
- **Interpretation:** The firm-level analogue of SGR (Damodaran and McKinsey's
  value-driver formula). Average the reinvestment rate over several years — capex is
  lumpy. A modeled quantity, not a screened one.
- **Sector notes:** 🏦 Not computable for financials.
- **Sources:** Damodaran (T2); McKinsey (T2).

### FCF Growth — EXTENDED

- **Formula:** YoY % / CAGR of FCF.
- **Interpretation:** Validates whether EPS growth is cash-backed. Too noisy to lead
  (capex timing, working-capital swings) — smooth over multiple years.
- **Sources:** CFA FCFF/FCFE definitions (T1); screener practice (T3).

### Operating Income Growth — EXTENDED

- **Formula:** YoY % / CAGR of Operating Income.
- **Interpretation:** The intermediate step: revenue growth vs operating-income growth
  exposes operating leverage; operating-income growth vs EPS growth exposes financing
  effects.
- **Sources:** McKinsey (T2); T3 screener sets.

---

## 8. Valuation

Is the stock cheap relative to its fundamentals? All ratios below are expressed in
**market-cap form**, computable from filings + the `market_cap` field in the stock
directory — no share-price feed needed.

**Enterprise Value (EV)**, used by several ratios:
**EV = Market Cap + Total Debt − Cash & Equivalents** (minimal form; refinements add
preferred equity and minority interest). Note that Damodaran and the CFA both hold that
**EV-based multiples are undefined for financials** — for banks and insurers use P/E and
P/B only.

**Choosing among multiples** (CFA/Damodaran guidance): different leverage across
comparables → prefer EV multiples over P multiples. Negative net income → fall back
EV/EBITDA → EV/Sales (or P/S) → P/B. Capital-intensive → check EV/EBIT, not just
EV/EBITDA. All multiples are TTM (trailing twelve months) — see implementation notes.

### P/E (Trailing) — CORE

- **Formula:** Market Cap ÷ Net Income TTM (refinement: net income available to common =
  net income − preferred dividends).
- **Inputs:** Net income (IS, four quarters); market cap.
- **Interpretation:** The most universally cited equity multiple. Low P/E = cheap per
  dollar of earnings — but justified P/E rises with expected growth and falls with risk,
  so a low P/E may signal low growth or high risk rather than mispricing. Undefined when
  earnings ≤ 0. Pitfalls: earnings are volatile and distortable — prefer normalized
  earnings; for cyclicals P/E is *lowest at the earnings peak* (the Molodovsky effect),
  the exact wrong moment to call it cheap.
- **Reference values:** Long-run US market average roughly 15–20×. <10× = priced for
  decline or deep value — verify earnings aren't at a cyclical peak; 20–30× = growth
  premium; >50× = speculative growth pricing or a trough-earnings artifact — treat as
  "unusual, inspect the earnings," not simply expensive.
- **Sector notes:** Fine for financials. 🏢 Misleading for REITs — P/FFO is the standard
  substitute.
- **Data difficulty:** Easy (+ TTM derivation).
- **Sources:** CFA Market-Based Valuation reading (T1); Damodaran relative-valuation
  notes (T2); Nareit (T3, REIT caveat).

### Earnings Yield — EXTENDED

- **Formulas:** E/P = Net Income TTM ÷ Market Cap (inverse of P/E). Greenblatt variant:
  **EBIT ÷ EV** (capital-structure-neutral; half of the Magic Formula, paired with
  return on capital).
- **Interpretation:** Same information as P/E but **defined even when earnings are
  negative**, so it ranks the full universe — CFA explicitly recommends E/P over P/E for
  ranking. Comparable against bond yields.
- **Reference values:** Compare against the 10-year Treasury yield: an earnings yield
  below the risk-free rate means paying a premium justified only by expected growth.
  EBIT/EV above ~10% is classic Greenblatt-cheap territory.
- **Sector notes:** EBIT/EV form 🏦 inapplicable to financials.
- **Sources:** CFA reading (T1); Greenblatt, *The Little Book That Beats the Market* (T2).

### P/B (Price-to-Book) — CORE

- **Formula:** Market Cap ÷ Common Shareholders' Equity (book equity − preferred).
  Variant: price-to-tangible-book (subtract goodwill and intangibles).
- **Inputs:** Equity (BS); market cap.
- **Interpretation:** <1 means trading below accounting net worth; justified P/B rises
  with ROE (the P/B↔ROE pair is the single most informative valuation-quality plot).
  Book value is stabler than earnings and usually positive. Weakness: historical-cost
  accounting and expensed intangibles understate true equity for asset-light/IP-heavy
  firms — P/B tells you little about a software company.
- **Sector notes:** 🏦 **More meaningful for financials** — bank assets are near fair
  value and regulatory capital is defined on book equity; Damodaran holds P/E and P/B
  are the *correct* multiples for banks. Foundation of the Fama-French value factor and
  the universe filter for Piotroski's F-Score.
- **Data difficulty:** Easy.
- **Sources:** CFA reading (T1); Damodaran, *Valuing Financial Service Firms* (T2);
  Fama-French / Piotroski (T2).

### P/S (Price-to-Sales) — CORE

- **Formula:** Market Cap ÷ Revenue TTM.
- **Inputs:** Revenue (IS); market cap.
- **Interpretation:** The fallback multiple when earnings and EBITDA are negative —
  sales are hard to fake and never negative (CFA rationale). Must be read jointly with
  margins: a high-margin and a zero-margin firm at the same P/S are not equally valued.
  Conceptual wrinkle: equity-level numerator over a firm-level denominator — **EV/Sales
  (EXTENDED) is the leverage-corrected version** CFA calls conceptually preferable; this
  doc keeps P/S core for familiarity and EV/Sales as the refinement.
- **Reference values:** <1× cheap per revenue dollar (or a low-margin business);
  ~1–2× typical for a mature company; >10× demands exceptional growth plus high
  margins — always read jointly with net margin (justified P/S ≈ net margin ×
  justified P/E).
- **Sector notes:** 🏦 Not for financials (revenue ill-defined). Cross-sector comparison
  invalid without margin context.
- **Data difficulty:** Medium (revenue chain + TTM).
- **Sources:** CFA reading (T1); Damodaran revenue-multiples notes (T2).

### EV/EBITDA — CORE

- **Formula:** EV ÷ EBITDA TTM.
- **Inputs:** BS (debt, cash), IS/CF (operating income, D&A); market cap.
- **Interpretation:** The standard operating multiple across capital structures — CFA:
  "more appropriate than P/E for comparing companies with different amounts of financial
  leverage"; the default in capital-intensive industries and M&A. Pitfall: EBITDA
  ignores capex, so it flatters capital-intensive firms — cross-check EV/EBIT.
- **Reference values:** Broad market typically ~8–12×; <6× cheap (or the market is
  pricing decline); >15× rich/growth-priced for a mature firm.
- **Sector notes:** 🏦 **Never for financials.** 🏢 REITs use the EBITDAre variant.
- **Data difficulty:** Hard (debt-tag fragmentation flows into EV).
- **Sources:** CFA reading (T1); Damodaran value-multiples notes (T2); Mauboussin,
  *Valuation Multiples* (T2/T3).

### EV/EBIT — EXTENDED

- **Formula:** EV ÷ Operating Income TTM.
- **Interpretation:** Like EV/EBITDA but charges for depreciation — penalizes capital
  intensity, so it better approximates sustainable operating profit where D&A is a real
  economic cost (Damodaran, Mauboussin). Its inverse is Greenblatt's earnings yield.
  Keep both: EV/EBITDA when D&A policies differ arbitrarily, EV/EBIT when capital
  intensity differs.
- **Reference values:** Typically ~10–14×; its inverse is the Greenblatt earnings
  yield — EBIT/EV >10% (EV/EBIT <10×) is classic "cheap" territory.
- **Sector notes:** 🏦 Not for financials.
- **Sources:** CFA reading (T1); Damodaran (T2); Greenblatt (T2).

### EV/Sales — EXTENDED

- **Formula:** EV ÷ Revenue TTM.
- **Interpretation:** The leverage-corrected P/S; use where EBITDA is negative
  (early-stage growth, distressed cyclicals). Interpret jointly with margins.
- **Reference values:** Same shape as the P/S bands: ~1–3× typical, >10× unusual
  (requires exceptional growth and margins); margin context is mandatory.
- **Sources:** CFA reading (T1); Damodaran (T2).

### FCF Yield — CORE

- **Formula:** FCF TTM ÷ Market Cap (equity form; P/FCF is its inverse). Firm form:
  FCF ÷ EV.
- **Inputs:** CFO, capex (CF); market cap.
- **Interpretation:** Valuation on actual cash generation — "cash flow is less subject
  to manipulation than earnings" (CFA). A wide gap between FCF yield and earnings yield
  is itself an accrual-quality flag. Volatile year to year; TTM smoothing helps.
- **Reference values:** >8% value territory (or the market doubts the cash flow's
  durability); 4–8% reasonable; <2% expensive or a heavy-reinvestment phase — check
  capex intensity before calling it overvalued. Compare against the 10-year Treasury
  yield as the risk-free alternative.
- **Sector notes:** 🏦 Meaningless for banks. 🏢 REITs: AFFO yield instead. Punishes
  firms in heavy growth-investment phases.
- **Data difficulty:** Easy.
- **Sources:** CFA reading (T1); Damodaran FCF primer (T2); Mauboussin (T2/T3).

### Dividend Yield + Payout Ratio — CORE

- **Formulas:** Dividend Yield = Common Dividends Paid TTM ÷ Market Cap (trailing-paid
  form from the CF statement — a faithful equivalent of the textbook per-share yield).
  Payout Ratio = Common Dividends Paid TTM ÷ Net Income TTM.
- **Inputs:** Dividends paid (CF, financing section); net income (IS); market cap.
- **Interpretation:** Read as a pair. Payout >100% (or greater than FCF) is
  unsustainable; extremely high yield usually signals an expected cut (value trap);
  payout links to growth via SGR = ROE × (1 − payout). A very low payout at a mature
  firm signals capacity to raise.
- **Reference values:** Yield ~2–4% is typical for dividend payers; >6–8% usually
  means the market is pricing a cut. Payout of 30–60% is the sustainable sweet spot
  for a mature payer.
- **Sector notes:** 🏢 REITs must pay ≥90% of taxable income — high payout is structural,
  and the denominator should be FFO, not net income. Yield is uninformative for
  no-dividend growth companies.
- **Data difficulty:** Medium — dividend tags split; absence of a tag usually (but not
  provably) means no dividend.
- **Sources:** CFA reading (T1); Damodaran dividend-policy notes (T2).

### Shareholder Yield — EXTENDED

- **Formula:** (Dividends Paid + Share Repurchases − Share Issuance) TTM ÷ Market Cap.
  All three flows sit in the CF financing section.
- **Interpretation:** Total capital returned to shareholders — buybacks are
  dividend-equivalent, and the academic net-payout-yield literature (Boudoukh, Michaely,
  Richardson & Roberts 2007) shows it predicts returns better than dividend yield alone.
  Use *net* of issuance: gross buybacks that merely offset stock-compensation dilution
  return nothing. Negative shareholder yield (net issuer) is itself a documented
  negative signal. One of the few metrics *more* natural in market-cap form than
  per-share form.
- **Reference values:** ~2–5% typical for a capital-returning firm; >5% aggressive
  capital return; negative = net issuer (the documented negative signal above).
- **Sources:** Boudoukh et al. 2007, *Journal of Finance* (T2); Faber, *Shareholder
  Yield* (T2/T3).

### PEG Ratio — EXCLUDED (documented for completeness)

- **Canonical formula:** (P/E) ÷ expected EPS growth % — which requires **analyst
  consensus forecasts the app does not have**. A trailing variant using historical EPS
  CAGR is computable but is *not* what Lynch/CFA/platforms mean by PEG, and historical
  growth forecasts poorly (Damodaran is critical of PEG even in canonical form).
  **Recommendation:** don't ship a misleading number — instead display P/E alongside
  revenue and EPS growth and let the user make the judgment PEG tries to automate.
- **Sources:** CFA reading (T1); Lynch (T2/T3); Damodaran (T2).

---

## 9. Composite Scores

Structured, research-backed ways to combine the base metrics into a single number. All
three CORE composites are fully computable from filings (+ market cap for Z-Score) using
two consecutive fiscal years.

### Piotroski F-Score — CORE

*Piotroski (2000), Journal of Accounting Research: nine binary signals, one point each,
score 0–9.*

**Profitability (4 points)**
1. ROA (net income ÷ beginning total assets) > 0
2. Operating cash flow ÷ total assets > 0
3. ROA improved vs prior year
4. CFO > net income (earnings backed by cash, not accruals)

**Leverage / liquidity / financing (3 points)**
5. Long-term debt ÷ average assets *decreased* vs prior year
6. Current ratio *increased* vs prior year
7. No common stock issued in the past year (no material issuance in the CF financing
   section / no rise in split-adjusted shares)

**Operating efficiency (2 points)**
8. Gross margin increased vs prior year
9. Asset turnover (revenue ÷ beginning assets) increased vs prior year

- **Interpretation:** 8–9 strong, 0–2 weak. Designed to be applied **within cheap (high
  book-to-market) stocks**, not the whole market. Original findings (1976–1996): high
  F-Score value stocks beat the value portfolio by ~7.5%/yr; effect strongest in small,
  neglected firms.
- **Reference values:** 8–9 strong, 3–7 middling (no signal either way), 0–2 weak;
  ≥7 is the common long-screen cutoff.
- **Sector notes:** 🏦 Built for non-financials — signals 5, 6, 8 are ill-defined for
  banks; exclude financials. 🏢 Partially applicable to REITs.
- **Sources:** Piotroski 2000 (T2); GMT Research / AAII implementations (T3).

### Altman Z-Score — CORE

*Altman (1968), Journal of Finance: bankruptcy-distress score. The original model wants
exactly the data this app has — X4's numerator is market cap.*

**Original model (public manufacturers):**

    Z = 1.2·X1 + 1.4·X2 + 3.3·X3 + 0.6·X4 + 1.0·X5

- X1 = Working Capital ÷ Total Assets (BS)
- X2 = Retained Earnings ÷ Total Assets (BS)
- X3 = EBIT ÷ Total Assets (IS, BS)
- X4 = **Market Cap ÷ Total Liabilities** (market data, BS)
- X5 = Revenue ÷ Total Assets (IS, BS)

**Thresholds:** Z > 2.99 safe · 1.81–2.99 grey zone · **Z < 1.81 distress**.

**Z″ variant (non-manufacturers):** Z″ = 6.56·X1 + 3.26·X2 + 6.72·X3 + 1.05·X4′
(X4′ uses *book* equity ÷ total liabilities; drops X5 to remove industry
asset-turnover effects). Thresholds: >2.6 safe · 1.1–2.6 grey · <1.1 distress.

- **Interpretation:** Predicts two-year bankruptcy probability (~95% accuracy one year
  out in the original sample). Implementation: original Z for manufacturers (SIC
  2000–3999), Z″ for other non-financials.
- **Sector notes:** 🏦 **Never for financials** — banks are excluded from all variants
  (leverage is their business model).
- **Sources:** Altman 1968; Altman, Hartzell & Peck 1995 (T2); Bloomberg/FactSet
  standard implementations (T3).

### DuPont Decomposition — CORE

*Not a score — the standard diagnostic attribution of ROE, and what makes ROE
interpretable.*

**3-factor:** ROE = Net Margin × Asset Turnover × Equity Multiplier
(NI/Revenue × Revenue/Avg Assets × Avg Assets/Avg Equity)

**5-factor:** ROE = Tax Burden × Interest Burden × EBIT Margin × Asset Turnover ×
Equity Multiplier (NI/EBT × EBT/EBIT × EBIT/Revenue × Revenue/Avg Assets ×
Avg Assets/Avg Equity)

- **Interpretation:** High ROE earned from **margin or turnover** is operationally
  earned (higher quality); high ROE driven mainly by the **equity multiplier** is
  leverage-manufactured (fragile). The 5-factor form separates operating performance
  from financing and tax effects. Trend analysis across years shows *why* ROE changed.
- **Sector notes:** Works for all sectors including financials — but bank equity
  multipliers are structurally huge; compare within sector. Terms uninterpretable with
  negative equity or negative pretax income.
- **Sources:** CFA L1 curriculum (T1); Penman (T2).

### Beneish M-Score — EXTENDED

*Beneish (1999), Financial Analysts Journal: earnings-manipulation probability. A red
flag, not a rating — surface as a warning, never a score to maximize.*

    M = −4.840 + 0.920·DSRI + 0.528·GMI + 0.404·AQI + 0.892·SGI
        + 0.115·DEPI − 0.172·SGAI − 0.327·LVGI + 4.679·TATA

Eight year-over-year indices, all from filings: DSRI (days-sales-in-receivables index),
GMI (gross margin index), AQI (asset quality index), SGI (sales growth index), DEPI
(depreciation index), SGAI (SG&A index), LVGI (leverage index), TATA (total accruals ÷
total assets — the dominant term).

- **Threshold:** M > −1.78 → flagged as a likely manipulator (−2.22 is the conservative
  cutoff). In-sample: caught ~76% of manipulators; famously flagged Enron ex ante.
- **Sector notes:** 🏦 Estimated on industrials; never score financials.
- **Sources:** Beneish 1999 (T2); GMT Research / Old School Value implementations (T3).
  Note: the TATA coefficient is 4.679 in the original paper; 4.697 circulates in
  secondary sources — use 4.679.

---

## 10. Summary Table

Tier: ★ = CORE, ☆ = EXTENDED. Mkt = needs market cap. 🏦 = invalid/adapted for
financials, 🏢 = caveat for REITs. Data = XBRL sourcing difficulty (E/M/H).

| Metric | Pillar | Tier | Mkt | 🏦 | 🏢 | Data |
|---|---|---|---|---|---|---|
| Gross profit margin | Profitability | ★ | | 🏦 | 🏢 | H |
| Operating profit margin | Profitability | ★ | | 🏦 | | E |
| Net profit margin | Profitability | ★ | | | 🏢 | M |
| Return on equity (ROE) | Profitability | ★ | | | 🏢 | E |
| Return on invested capital (ROIC) | Profitability | ★ | | 🏦 | 🏢 | M |
| EBITDA margin | Profitability | ☆ | | 🏦 | 🏢 | M |
| Return on assets (ROA) | Profitability | ☆ | | | 🏢 | E |
| Total asset turnover | Efficiency | ★ | | 🏦 | | E |
| Cash conversion cycle (+ DIO, DSO, DPO) | Efficiency | ★ | | 🏦 | 🏢 | M |
| Fixed asset turnover | Efficiency | ☆ | | 🏦 | | E |
| Working capital turnover | Efficiency | ☆ | | 🏦 | | E |
| Current ratio | Liquidity | ★ | | 🏦 | 🏢 | E |
| Quick ratio | Liquidity | ★ | | 🏦 | 🏢 | M |
| Operating cash flow ratio | Liquidity | ★ | | 🏦 | | E |
| Cash ratio | Liquidity | ☆ | | 🏦 | | M |
| Working capital (level) | Liquidity | ☆ | | 🏦 | | E |
| Defensive interval ratio | Liquidity | ☆ | | 🏦 | | M |
| Debt-to-equity | Solvency | ★ | | 🏦 | 🏢 | H |
| Net debt / EBITDA | Solvency | ★ | | 🏦 | 🏢 | H |
| Interest coverage (EBIT/interest) | Solvency | ★ | | 🏦 | | M |
| Debt-to-capital / debt-to-assets | Solvency | ☆ | | 🏦 | | H |
| Financial leverage (equity multiplier) | Solvency | ☆ | | | | E |
| EBITDA/interest coverage | Solvency | ☆ | | 🏦 | | M |
| CFO / total debt | Solvency | ☆ | | 🏦 | | H |
| Free cash flow (CFO − capex) | Cash flow | ★ | | 🏦 | 🏢 | E |
| FCF margin | Cash flow | ★ | | 🏦 | 🏢 | M |
| CFO / net income (+ Sloan accruals) | Cash flow | ★ | | 🏦 | 🏢 | E |
| FCF conversion | Cash flow | ☆ | | 🏦 | | M |
| Capex intensity | Cash flow | ☆ | | 🏦 | 🏢 | M |
| Revenue growth | Growth | ★ | | | 🏢 | M |
| EPS growth | Growth | ★ | | | 🏢 | E |
| Sustainable growth rate | Growth | ☆ | | | | E |
| Reinvestment-rate growth | Growth | ☆ | | 🏦 | | M |
| FCF growth | Growth | ☆ | | 🏦 | 🏢 | E |
| Operating income growth | Growth | ☆ | | 🏦 | | E |
| P/E (trailing) | Valuation | ★ | ✓ | | 🏢 | E |
| P/B | Valuation | ★ | ✓ | | | E |
| P/S | Valuation | ★ | ✓ | 🏦 | | M |
| EV/EBITDA | Valuation | ★ | ✓ | 🏦 | 🏢 | H |
| FCF yield | Valuation | ★ | ✓ | 🏦 | 🏢 | E |
| Dividend yield + payout ratio | Valuation | ★ | ✓ | | 🏢 | M |
| Earnings yield (E/P, EBIT/EV) | Valuation | ☆ | ✓ | 🏦 | | M |
| EV/EBIT | Valuation | ☆ | ✓ | 🏦 | | H |
| EV/Sales | Valuation | ☆ | ✓ | 🏦 | | H |
| Shareholder yield | Valuation | ☆ | ✓ | | | M |
| PEG | Valuation | — | ✓ | | | excluded (needs estimates) |
| Piotroski F-Score | Composite | ★ | | 🏦 | 🏢 | M |
| Altman Z-Score | Composite | ★ | ✓ | 🏦 | 🏢 | M |
| DuPont decomposition | Composite | ★ | | | | E |
| Beneish M-Score | Composite | ☆ | | 🏦 | 🏢 | M |

Core count: 24 metrics + 3 composites.

---

## 11. Implementation Notes: SEC EDGAR Data

Practical notes for the next phase, verified against the live APIs (August 2026).

### Data access

- **APIs** (`data.sec.gov`, JSON, no key): `companyfacts/CIK##########.json` (every
  standard-taxonomy fact a company ever filed — the workhorse), `companyconcept/…`
  (one company × one concept), `frames/us-gaap/<Concept>/USD/CY2023Q1.json` (one fact
  per filer for a calendar period). CIKs are 10-digit zero-padded; map tickers via
  `https://www.sec.gov/files/company_tickers.json`.
- **Fair-access rules:** max **10 requests/second**, and a declared User-Agent of the
  form `AppName contact@email.com` is mandatory — generic UAs get 403'd.
- **Bulk:** nightly `companyfacts.zip` (~1GB+) beats crawling per company for
  full-universe work. The quarterly *Financial Statement Data Sets* are an alternative
  that also includes custom extension tags and segment detail the JSON APIs omit.
- **Important limitation:** the JSON APIs exclude filer-specific extension tags and
  dimensioned (segment / per-share-class) facts. Usually a feature (consolidated
  totals only), occasionally a gap.

### The five pitfalls that will actually bite

1. **Revenue needs a fallback chain.** No single tag exceeds ~49% filer coverage. Use,
   in order: `RevenueFromContractWithCustomerExcludingAssessedTax` → `Revenues` →
   `RevenueFromContractWithCustomerIncludingAssessedTax`; pre-2018 history lives under
   the deprecated `SalesRevenueNet` family and must be stitched. Similar (worse)
   fragmentation affects **debt** (8+ tags, double-count risk) and **D&A** (3 tag
   families) — this is why those metrics are marked Data: Hard.
2. **There is no Q4 filing.** 10-Ks report full-year figures; Q4 flows must be computed
   as FY − (Q1+Q2+Q3). 10-Q cash-flow statements are year-to-date, so Q2/Q3 CFO and
   capex also need differencing. Filter by fact duration (~80–100 days = a true
   quarter) rather than trusting fiscal-period labels.
3. **TTM is your job.** No endpoint serves trailing-twelve-month values. Compute as
   most recent FY − prior-year YTD + current YTD (or sum four derived quarters). All
   valuation multiples in §8 assume TTM flow denominators paired with the latest
   balance sheet.
4. **Detect financials structurally, don't just flag them.** Banks/insurers have *no*
   `AssetsCurrent`/`LiabilitiesCurrent` facts at all (verified: JPMorgan returns zero),
   no COGS, often no `OperatingIncomeLoss`. Detect via SIC code in the submissions
   JSON (or the directory's sector field) and **suppress** inapplicable metrics rather
   than emitting nulls or nonsense.
5. **Deduplicate and mind restatements.** The same (concept, period) appears multiple
   times in companyfacts — original filing, later comparative re-reports, and
   amendments, possibly with different values. Take the latest `filed` per (concept,
   start, end); for any future backtesting, note that using restated values introduces
   look-ahead bias.

### Input reliability (measured, CY2023, ~6,400 filers)

- **Near-universal single tags:** `Assets`, `NetIncomeLoss`, CFO
  (`NetCashProvidedByUsedInOperatingActivities`), `StockholdersEquity`, EPS, weighted
  share counts, `IncomeTaxExpenseBenefit`, `OperatingIncomeLoss`.
- **Short fallback chain or derivation:** revenue, total liabilities (derive from
  `LiabilitiesAndStockholdersEquity` − equity), current assets/liabilities
  (structural gap = financials), capex, receivables/payables, dividends/buybacks
  (absence usually means "didn't do it").
- **Fragmented / best-effort:** cost of revenue & gross profit, D&A, short/long-term
  debt components, interest expense (~56% direct), short-term investments,
  parent-vs-consolidated equity and income (`NetIncomeLoss` vs `ProfitLoss`,
  minority interest), pre-2018 revenue history.

---

## 12. Bibliography

**Tier 1 — professional body**
- CFA Institute, *Financial Analysis Techniques* (refresher reading) —
  https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/financial-analysis-techniques
- CFA Institute, *Market-Based Valuation: Price and Enterprise Value Multiples* —
  https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/market-based-valuation-price-enterprise-value-multiples
- CFA Institute, *Free Cash Flow Valuation* —
  https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/free-cash-flow-valuation
- CFA Institute, official Financial Ratio List (Level II) —
  https://www.cfainstitute.org/sites/default/files/-/media/documents/support/programs/cfa/cfa_program_level_ii_financial_ratio_list.pdf

**Tier 2 — academic & practitioner canon**
- Damodaran, A., *Return on Capital (ROC), ROIC and ROE: Measurement and Implications* —
  https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/returnmeasures.pdf
- Damodaran, A., *Valuing Financial Service Firms* —
  https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf
- Damodaran, A., synthetic ratings (interest coverage → rating) —
  https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.htm
- Damodaran, A., relative valuation & value multiples lecture notes —
  https://pages.stern.nyu.edu/~adamodar/pdfiles/eqnotes/vebitda.pdf
- Damodaran, A., *Fundamental Determinants of Growth* —
  https://pages.stern.nyu.edu/~adamodar/New_Home_Page/invfables/growthdeterminants.htm
- McKinsey & Company, *Valuation* value-driver framework; "How to choose between growth
  and ROIC" — mckinsey.com
- Penman, S., *Financial Statement Analysis and Security Valuation* (ratio
  decomposition, accruals research)
- Graham, B., *The Intelligent Investor* (defensive-investor criteria, via
  grahamvalue.com)
- Piotroski, J. (2000), "Value Investing: The Use of Historical Financial Statement
  Information to Separate Winners from Losers," *Journal of Accounting Research* 38.
- Altman, E. (1968), "Financial Ratios, Discriminant Analysis and the Prediction of
  Corporate Bankruptcy," *Journal of Finance* 23(4); Altman, Hartzell & Peck (1995) Z″.
- Beneish, M. (1999), "The Detection of Earnings Manipulation," *Financial Analysts
  Journal* 55(5).
- Sloan, R. (1996), "Do Stock Prices Fully Reflect Information in Accruals and Cash
  Flows about Future Earnings?" *The Accounting Review* 71(3).
- Boudoukh, Michaely, Richardson & Roberts (2007), "On the Importance of Measuring
  Payout Yield," *Journal of Finance*.
- Greenblatt, J., *The Little Book That Beats the Market* (Magic Formula).
- Mauboussin, M., *Valuation Multiples* (Morgan Stanley Counterpoint Global) —
  https://www.morganstanley.com/im/publication/insights/articles/article_valuationmultiples.pdf

**Tier 3 — professional practice**
- Moody's, *Putting EBITDA Into Perspective* (2000).
- Nareit, FFO White Paper (2018) — https://www.reit.com/glossary/funds-operation-ffo
- S&P/credit-practice leverage tiers; Wall Street Prep, GMT Research, AAII, Faber
  *Shareholder Yield* implementations.

**SEC data documentation**
- EDGAR APIs — https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- Fair access / rate limits — https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- Financial Statement Data Sets —
  https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets
