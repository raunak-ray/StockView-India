from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources

DATA_PACKAGE = "app.modules.instruments.data"
ASSET_NAME = "instrument_master.json"


@lru_cache(maxsize=1)
def _load_asset() -> tuple[dict[str, str], dict[str, list[list]]]:
    raw = resources.files(DATA_PACKAGE).joinpath(ASSET_NAME).read_text(encoding="utf-8")
    payload = json.loads(raw)
    return payload["stocks"], payload["nifty50_sectors"]


def all_stocks() -> dict[str, str]:
    """Full curated NSE/BSE name -> Yahoo ticker map (insertion order preserved)."""
    return _load_asset()[0]


def search_stocks(query: str, limit: int = 50) -> list[dict[str, str]]:
    """Case-insensitive substring match on name or ticker.

    Parity with the sidebar filter in app.py:926-930:
        filtered = {k: v for k, v in ALL_STOCKS.items()
                    if q in k.lower() or q in v.lower()}
    Results keep the instrument master's original order.
    """
    q = query.strip().lower()
    if not q:
        return []
    matches = [
        {"name": name, "ticker": ticker}
        for name, ticker in all_stocks().items()
        if q in name.lower() or q in ticker.lower()
    ]
    return matches[:limit]


def nifty50_sectors() -> dict[str, list[list]]:
    """NIFTY 50 sector groupings: sector -> [[ticker, label, mcap], ...]."""
    return _load_asset()[1]
