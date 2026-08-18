"""Batch builder for the local stock directory.

Fetches every US-listed stock (NASDAQ, NYSE, AMEX) from the Nasdaq screener
bulk endpoint -- one request per exchange, three requests total -- and writes
data/stock_directory.json mapping ticker -> exchange, sector, industry, etc.

Run any time to refresh: uv run build-directory
"""

import json
import os
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

from stock_analyst.stock_directory import DEFAULT_PATH

_SCREENER_URL = "https://api.nasdaq.com/api/screener/stocks"
_EXCHANGES = ["NASDAQ", "NYSE", "AMEX"]
# Write where the runtime lookup reads, so the two can never disagree.
_OUTPUT_PATH = DEFAULT_PATH

# The endpoint hangs on default python UAs; a browser-like UA is required.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "application/json",
}
_TIMEOUT_SECONDS = 30
_MAX_ATTEMPTS = 3
# Abort rather than clobber a good directory if the endpoint returns a
# suspiciously small result set.
_MIN_TOTAL_COUNT = 5000


def _normalize_ticker(symbol: str) -> str:
    """Canonical ticker form: uppercase, share classes as dots (BRK/A -> BRK.A)."""
    return symbol.strip().upper().replace("/", ".")


def _fetch_exchange(exchange: str) -> list[dict]:
    params = {"tableonly": "true", "limit": 25, "exchange": exchange, "download": "true"}
    last_error: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = requests.get(
                _SCREENER_URL, params=params, headers=_HEADERS, timeout=_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            rows = response.json()["data"]["rows"]
            if not rows:
                raise ValueError(f"screener returned zero rows for {exchange}")
            return rows
        except (requests.RequestException, KeyError, ValueError) as error:
            last_error = error
            if attempt < _MAX_ATTEMPTS:
                delay = 2**attempt
                print(f"  {exchange}: attempt {attempt} failed ({error}); retrying in {delay}s")
                time.sleep(delay)
    raise RuntimeError(f"failed to fetch {exchange} after {_MAX_ATTEMPTS} attempts: {last_error}")


def _parse_market_cap(raw: str) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value or None


def _parse_ipo_year(raw: str) -> int | None:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _build_directory() -> dict:
    stocks: dict[str, dict] = {}
    counts: dict[str, int] = {}
    for exchange in _EXCHANGES:
        print(f"Fetching {exchange}...")
        rows = _fetch_exchange(exchange)
        counts[exchange] = len(rows)
        for row in rows:
            ticker = _normalize_ticker(row["symbol"])
            if ticker in stocks:
                print(
                    f"  duplicate ticker {ticker}: keeping "
                    f"{stocks[ticker]['exchange']}, ignoring {exchange}"
                )
                continue
            stocks[ticker] = {
                "name": row.get("name") or None,
                "exchange": exchange,
                "sector": row.get("sector") or None,
                "industry": row.get("industry") or None,
                "country": row.get("country") or None,
                "market_cap": _parse_market_cap(row.get("marketCap")),
                "ipo_year": _parse_ipo_year(row.get("ipoyear")),
            }
        print(f"  {exchange}: {len(rows)} rows")

    counts["total"] = len(stocks)
    if counts["total"] < _MIN_TOTAL_COUNT:
        raise RuntimeError(
            f"only {counts['total']} tickers fetched (expected >= {_MIN_TOTAL_COUNT}); "
            "refusing to overwrite the directory"
        )

    return {
        "metadata": {
            "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "source": "nasdaq-screener",
            "counts": counts,
        },
        "stocks": dict(sorted(stocks.items())),
    }


def _write_atomic(directory: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(directory, handle, indent=1)
            handle.write("\n")
        os.replace(temp_path, path)
    except BaseException:
        os.unlink(temp_path)
        raise


def _main() -> int:
    try:
        directory = _build_directory()
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    _write_atomic(directory, _OUTPUT_PATH)
    counts = directory["metadata"]["counts"]
    print(
        f"Wrote {counts['total']} tickers to {_OUTPUT_PATH} "
        f"({', '.join(f'{k}: {v}' for k, v in counts.items() if k != 'total')})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(_main())
