"""The stock universe the news scraper covers.

Scope decision: **NSE Nifty 100 intersected with the app's existing instrument
master**. The intersection is 86 stocks, not 100 — 14 Nifty 100 members are
absent from the app's 646-entry list (`ADANIENSOL`, `BAJAJHLDNG`, `ETERNAL`,
`GRASIM`, `HINDZINC`, `POWERINDIA`, `HYUNDAI`, `JIOFIN`, `LTM`, `ENRIN`,
`TATACAP`, `TMCV`, `TMPV`, `VAML`). Rather than scraping symbols the app cannot
show, we store a checked-in snapshot so the scraper stays deterministic and the
tests need no network.

Snapshot source: NSE's official `ind_nifty100list.csv`. Refresh by re-running
the intersect against a fresh download — see `plan/07-news-plan.md`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources

DATA_PACKAGE = "app.modules.news.data"
ASSET_NAME = "nifty100_symbols.json"


@dataclass(frozen=True, slots=True)
class Target:
    """One stock to scrape, with the names we need to build search queries."""

    symbol: str  # "RELIANCE.NS" — the app's ticker format
    base_symbol: str  # "RELIANCE" — bare NSE symbol
    display_name: str  # "Reliance Industries" — the app's curated name
    nse_name: str  # "Reliance Industries Ltd." — official NSE name
    industry: str  # "Oil Gas & Consumable Fuels"

    def query_terms(self) -> tuple[str, ...]:
        """Ordered search queries, most precise first.

        Ladder rationale, in order of measured behaviour:
          1. official NSE name + NSE — the precise form; the `"… Limited"` suffix
             is stripped because quoted company names often over-filter.
          2. curated app name — differs from the NSE name for some symbols and
             occasionally matches where the official name does not.
          3. bare symbol + "shares" — last resort, noisier, so it is gated by
             the relevance filter in `service.py`.

        Each rung is recorded per-article in `NewsArticle.query_used` so a bad
        match can be traced rather than silently accepted.
        """
        terms = [
            f'"{_strip_suffix(self.nse_name)}" NSE',
            f'"{self.display_name}" stock India',
            f"{self.base_symbol} shares NSE",
        ]
        # Drop rungs that would duplicate an earlier one.
        seen: set[str] = set()
        unique: list[str] = []
        for term in terms:
            if term not in seen:
                seen.add(term)
                unique.append(term)
        return tuple(unique)


def _strip_suffix(company_name: str) -> str:
    """Drop trailing corporate suffixes that hurt search precision."""
    for suffix in (" Ltd.", " Limited", " Ltd", " ltd."):
        if company_name.endswith(suffix):
            return company_name[: -len(suffix)]
    return company_name


@lru_cache(maxsize=1)
def _load_asset() -> dict:
    raw = resources.files(DATA_PACKAGE).joinpath(ASSET_NAME).read_text(encoding="utf-8")
    return json.loads(raw)


def targets() -> list[Target]:
    """Every stock in scope for scraping, in Nifty 100 rank order."""
    return [Target(**row) for row in _load_asset()["stocks"]]


def coverage() -> dict[str, object]:
    """Provenance metadata — how many Nifty 100 members we cover and why not more."""
    asset = _load_asset()
    return {
        "source": asset["source"],
        "fetched_on": asset["fetched_on"],
        "nifty100_total": asset["nifty100_total"],
        "covered": asset["covered"],
        "note": asset["note"],
    }


def by_symbol(symbol: str) -> Target | None:
    """Look up a single target by full or bare symbol."""
    clean = symbol.strip().upper()
    for target in targets():
        if clean in (target.symbol.upper(), target.base_symbol.upper()):
            return target
    return None
