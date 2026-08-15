# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

An agent-based fundamental stock analyst: LLM agents parse SEC quarterly reports (10-Q PDFs) into structured raw values, pure Python functions compute fundamental-analysis metrics from them, and interpretation agents read the results. Built on LangChain/LangGraph; agent prompting is currently prototyped in `prompting_experiments.ipynb` before moving into the codebase.

## Commands

Dependencies are managed with `uv` (Python 3.12+):

```sh
uv sync                                            # install deps (incl. dev group)
uv run pytest                                      # run all tests
uv run pytest tests/test_metrics.py                # one file
uv run pytest tests/test_metrics.py::test_name     # one test
uv run python build_directory.py                   # rebuild data/stock_directory.json (network)
```

`pyproject.toml` sets `pythonpath = ["."]` for pytest, so the flat repo layout imports during collection.

Secrets (OpenAI key, `USE_LOCAL_LLM` toggle for Ollama) live in `.env` (gitignored). `sandbox/` holds sample filing PDFs for experiments and is also gitignored.

## Architecture

The pipeline for one company and one reporting period:

```
10-Q PDF ──(parsing agent)──▶ QuarterlyReportParseResult ─┐
                                                          ├─▶ run_all_calculations() ─▶ CalculatedMetrics ─▶ (interpretation agent)
stock_directory.lookup(ticker) ─▶ StockInfo (market cap) ─┘
```

- **`quarterly_report_parse_result.py`** — frozen pydantic model of every raw *leaf* value the metrics need, one instance per reporting period. Field descriptions are written *for the parsing agent* (where the value appears in a filing, synonym labels filers use); notes mapping fields to `metrics.py` parameters are code comments. Deliberately excludes intermediates that `metrics.py` computes, market data, and prior-period/average inputs. Also has `merge`, `get_diffs`, and `count_populated_fields` for comparing parses across prompting experiments.
- **`metrics.py`** — pure calculation functions, one per metric in `docs/fundamental_metrics.md` (seven pillars plus composite scores like Altman Z and Piotroski F). No I/O; callers wire in values.
- **`run_all_calculations.py`** — wires a `StockInfo` + one parse result through every currently computable metric, producing a `CalculatedMetrics`.
- **`calculated_metrics.py`** — frozen pydantic output model, one field per computed metric. Field descriptions are written *for interpretation agents*: definition, unit, reference bands, sector caveats.
- **`build_directory.py` / `stock_directory.py`** — batch builder (3 HTTP requests to the Nasdaq screener, one per exchange) writes `data/stock_directory.json`; the runtime module answers ticker lookups from that file with no network. `StockInfo.market_cap` is the one metric input not parseable from a filing. Refreshing the directory has a dedicated skill: `.claude/skills/update-stock-directory`.

### Docs are part of the design

- `docs/fundamental_metrics.md` — the authority on *what* each metric means, its formula, and interpretation; the pydantic field descriptions distill it.
- `docs/calculation_notes.md` — *how* `metrics.py` implements it and why.
- `docs/descoped_multi_period_metrics.md` — the current scope is a **single quarterly report per run**. Metrics needing average balances, prior-period values, or period-over-period changes exist in `metrics.py` but have no `CalculatedMetrics` fields and are not wired in `run_all_calculations.py`. This doc is the checklist (with restore procedure) for when multi-report support lands — follow it rather than re-deriving.

## Conventions

These span all the modules above and must stay consistent:

- **No abbreviations in identifiers** — spell names out in full, even EBITDA/NOPAT/capex (`earnings_before_interest_taxes_depreciation_and_amortization`). Docstrings note the common short form.
- **`None` propagation** — every value defaults to `None` (not reported / not computable); every metric function returns `None` when an input is `None`, a denominator is zero, or the metric is not meaningful (e.g. price-to-earnings on negative earnings). This mirrors gaps in real XBRL data.
- **Zero-if-missing is the caller's decision, not the parser's** — `run_all_calculations.py` treats usually-absent components (lease obligations, preferred equity/dividends, minority interest, short-term investments) as `0.0` when `None`, but *not* dividends, buybacks, or stock issuance (an absent tag is not provably a zero flow).
- **Signs** — capital expenditures, dividends paid, buybacks, and stock issuance are positive magnitudes; `investing_cash_flow` keeps its statement sign (usually negative).
- **Units** — absolute amounts in the filing's currency (not per-share, except `earnings_per_share`); ratios are decimal fractions (0.25 == 25%); day-count metrics return days.
- **Period** — flow values in a parse result are fiscal-year-to-date (the only period a 10-Q's cash flow statement provides — never mix in single-quarter columns); balance-sheet values are as of the period end. True single-quarter flows require differencing consecutive parse results, like the other descoped multi-period inputs.
