---
name: update-stock-directory
description: Refresh the local stock directory data file, stored at data/stock_directory.json, so that it has the latest information on all US-listed stocks. Information such as exchange, sector, industry, and market cap. Use this skill when the user explicitly asks to update, refresh, or rebuild the stock directory, or when the directory is stale or missing.
---

# Update Stock Directory

Refresh the local stock directory (`data/stock_directory.json`) from the free Nasdaq screener bulk endpoint. The whole update is 3 HTTP requests (one per exchange: NASDAQ, NYSE, AMEX) — never fetch per-stock data.

## Steps

1. **Check the current state** (skip gracefully if the file doesn't exist yet — that just means this is the first build):

   ```bash
   uv run python -c "import json; m = json.load(open('data/stock_directory.json'))['metadata']; print(m['built_at'], m['counts'])"
   ```

   If `built_at` is less than 24 hours old, tell the user the directory is already fresh and ask whether to rebuild anyway — listings data rarely changes intraday.

2. **Run the batch builder** from the repo root:

   ```bash
   uv run python build_directory.py
   ```

   Takes ~10–30 seconds. It retries each exchange 3 times with backoff, writes atomically, and refuses to overwrite the existing file if it fetches fewer than 5,000 tickers total — so a failure here never corrupts the existing directory.

3. **Verify** the refreshed directory:

   ```bash
   uv run python -c "
   from stock_directory import lookup
   assert lookup('AAPL').exchange == 'NASDAQ' and lookup('AAPL').sector == 'Technology'
   assert lookup('JPM').exchange == 'NYSE'
   assert lookup('NOTREAL') is None
   print('lookups OK')
   "
   ```

4. **Summarize what changed.** If the previous version is in git, diff ticker sets:

   ```bash
   uv run python -c "
   import json, subprocess
   old = json.loads(subprocess.run(['git', 'show', 'HEAD:data/stock_directory.json'], capture_output=True, text=True).stdout or '{\"stocks\": {}}')['stocks']
   new = json.load(open('data/stock_directory.json'))['stocks']
   added, removed = sorted(set(new) - set(old)), sorted(set(old) - set(new))
   print(f'{len(added)} added: {added[:20]}')
   print(f'{len(removed)} removed: {removed[:20]}')
   "
   ```

   Report to the user: per-exchange counts, total, number of tickers added/removed (name a few — new listings and delistings are interesting), and the new `built_at`.

5. **Do not commit** unless the user asks. If they do, commit `data/stock_directory.json` alone with a message like `Refresh stock directory (7,110 tickers, 2026-08-12)`.

## Troubleshooting

- **All three exchanges fail / timeouts**: the endpoint (`api.nasdaq.com/api/screener/stocks`) requires a browser-like User-Agent, which `build_directory.py` already sends. Persistent failure likely means Nasdaq changed the unofficial endpoint — check whether the response shape still has `data.rows` with `symbol`/`sector`/`industry` fields, and fix `build_directory.py` to match.
- **Endpoint gone entirely**: the documented fallback is SEC EDGAR — `https://www.sec.gov/files/company_tickers_exchange.json` for ticker/exchange plus SIC codes for industry (requires a `User-Agent: name email` header). This is a rebuild of the source layer, not a quick fix; surface it to the user before attempting.
- **Count sanity check trips** (< 5,000 tickers): one exchange probably returned a partial result. The old file is untouched; just rerun.
