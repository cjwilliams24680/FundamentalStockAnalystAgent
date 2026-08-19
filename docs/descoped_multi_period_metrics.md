# Descoped Metrics: Calculations Requiring Multiple Quarterly Reports

The current scope of the app processes a **single quarterly report** per run. The
calculations below all need inputs that one report cannot provide — average
balance-sheet values (beginning and ending balances from two consecutive
reports), prior-period flows, or period-over-period changes — so they have been
**descoped until multiple reports are supported**.

Nothing here is lost: the calculation functions all exist in `calculations.py` and
their interpretation guidance is in `docs/fundamental_metrics.md`. This list is
the checklist for re-adding them when multi-report support lands. To restore
one:

1. Re-add its field to `CalculatedValues` in `calculated_values.py` (the
   field definitions with their interpretation-agent descriptions are in git
   history, and the reference bands are in `docs/fundamental_metrics.md`).
2. Wire the call in `calculations_runner.py`, building the multi-period
   inputs from two (or more) parse results — `calculations.average` exists for
   the average-balance inputs.

## Profitability

| Calculation | `calculations.py` function | Missing multi-period input |
|---|---|---|
| Return on equity | `return_on_equity` | Average shareholders' equity (two consecutive balance sheets) |
| Return on assets | `return_on_assets` | Average total assets |
| Return on invested capital | `return_on_invested_capital` | Average invested capital |

## Efficiency

| Calculation | `calculations.py` function | Missing multi-period input |
|---|---|---|
| Total asset turnover | `total_asset_turnover` | Average total assets |
| Fixed asset turnover | `fixed_asset_turnover` | Average net fixed assets |
| Working capital turnover | `working_capital_turnover` | Average working capital |
| Days inventory on hand | `days_inventory_on_hand` | Average inventory |
| Days sales outstanding | `days_sales_outstanding` | Average receivables |
| Purchases | `purchases` | Change in inventory (ending minus beginning) |
| Days payables outstanding | `days_payables_outstanding` | Average payables, plus purchases above |
| Cash conversion cycle | `cash_conversion_cycle` | The three day counts above |

## Solvency & leverage

| Calculation | `calculations.py` function | Missing multi-period input |
|---|---|---|
| Financial leverage (equity multiplier) | `financial_leverage` | Average total assets and average total equity |

## Growth

| Calculation | `calculations.py` function | Missing multi-period input |
|---|---|---|
| Revenue growth | `growth_rate` | Prior-period revenue |
| Earnings per share growth | `growth_rate` | Prior-period earnings per share |
| Operating income growth | `growth_rate` | Prior-period operating income |
| Free cash flow growth | `growth_rate` | Prior-period free cash flow |
| Sustainable growth rate | `sustainable_growth_rate` | Return on equity (average equity, above) |
| Reinvestment rate | `reinvestment_rate` | Change in working capital |
| Fundamental growth | `fundamental_growth` | Reinvestment rate and return on invested capital, both above |

Multi-year history would additionally enable `compound_annual_growth_rate`,
which was excluded from `CalculatedValues` from the start for the same reason.

## Composite scores

| Calculation | `calculations.py` function | Missing multi-period input |
|---|---|---|
| Piotroski F-Score | `piotroski_f_score` | Full prior-year input set (all nine signals compare two years) |
| DuPont three-factor decomposition | `dupont_three_factor` | Average total assets and average total equity |
| DuPont five-factor decomposition | `dupont_five_factor` | Average total assets and average total equity |
| Beneish M-Score | `beneish_m_score` | A complete `BeneishPeriod` for both the current and prior year |

Note the dependency chains when re-adding: the cash conversion cycle needs the
three day counts; sustainable growth needs return on equity; fundamental growth
needs both the reinvestment rate and return on invested capital. Restore leaf
metrics first.
