from __future__ import annotations

import pytest

from app.modules.instruments import service


@pytest.fixture(scope="module")
def stocks() -> dict[str, str]:
    return service.all_stocks()


def test_asset_loads_and_is_well_formed(stocks):
    assert len(stocks) > 500
    assert all(
        isinstance(name, str) and isinstance(ticker, str) and ticker
        for name, ticker in stocks.items()
    )
    # Parity spot-checks against app.py's ALL_STOCKS (verbatim extraction).
    assert stocks["Nifty 50"] == "^NSEI"
    assert stocks["TCS"] == "TCS.NS"
    assert stocks["HDFC Bank"] == "HDFCBANK.NS"


def test_search_matches_name_case_insensitive(stocks):
    results = service.search_stocks("reliance")
    tickers = [r["ticker"] for r in results]
    assert "RELIANCE.NS" in tickers


def test_search_matches_ticker_substring(stocks):
    results = service.search_stocks("tcs.ns")
    assert any(r["name"] == "TCS" for r in results)


def test_search_no_match_returns_empty():
    assert service.search_stocks("zzzznotaticker") == []


def test_search_empty_query_returns_empty():
    assert service.search_stocks("") == []
    assert service.search_stocks("   ") == []


def test_search_respects_limit():
    results = service.search_stocks("bank", limit=3)
    assert len(results) <= 3


def test_sectors_available():
    sectors = service.nifty50_sectors()
    assert set(sectors) >= {"IT", "Financial Services", "Oil & Gas"}
