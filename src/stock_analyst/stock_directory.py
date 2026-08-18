"""Runtime lookup API for the local stock directory.

Loads data/stock_directory.json (built by build_directory.py) once and answers
ticker -> exchange/industry lookups with no network calls.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from stock_analyst.paths import DATA_DIRECTORY

DEFAULT_PATH = DATA_DIRECTORY / "stock_directory.json"

_directory: dict | None = None


@dataclass(frozen=True)
class StockInfo:
    ticker: str
    name: str | None
    exchange: str
    sector: str | None
    industry: str | None
    country: str | None
    market_cap: float | None
    ipo_year: int | None


def _normalize_ticker(symbol: str) -> str:
    """Canonical ticker form: uppercase, share classes as dots (BRK/A -> BRK.A)."""
    return symbol.strip().upper().replace("/", ".")


def _load_directory(path: Path | str = DEFAULT_PATH) -> dict:
    """Load (and cache) the directory. Raises FileNotFoundError with a hint
    if the batch builder has not been run yet."""
    global _directory
    if _directory is None:
        try:
            with open(path) as handle:
                _directory = json.load(handle)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"{path} not found -- run `python build_directory.py` first"
            ) from None
    return _directory


def lookup(ticker: str) -> StockInfo | None:
    """Return StockInfo for a ticker, or None if it is not a US-listed stock."""
    directory = _load_directory()
    canonical = _normalize_ticker(ticker)
    record = directory["stocks"].get(canonical)
    if record is None:
        return None
    return StockInfo(ticker=canonical, **record)
