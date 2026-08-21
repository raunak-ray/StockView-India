from __future__ import annotations

import math

import pandas as pd
import pytest
from fastapi import HTTPException

import app.modules.market_data.service as svc


@pytest.fixture(autouse=True)
def _no_cache(monkeypatch):
    """Keep unit tests hermetic: bypass the Redis layer entirely."""

    async def fake_cache_get(_key: str):
        return None

    async def fake_cache_set(_key: str, _value, _ttl: int) -> None:
        return None

    monkeypatch.setattr(svc, "cache_get", fake_cache_get)
    monkeypatch.setattr(svc, "cache_set", fake_cache_set)


# ── Helpers ───────────────────────────────────────────────────────────────────


def close_frame(dates, syms, rows) -> pd.DataFrame:
    cols = pd.MultiIndex.from_product([["Close"], syms])
    return pd.DataFrame(rows, index=dates, columns=cols)


def ohlcv_with_yf_columns(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Wrap a flat OHLCV frame the way yfinance does (field, ticker) columns."""
    out = df.copy()
    out.columns = pd.MultiIndex.from_product(
        [list(df.columns), [ticker]]
    )
    return out


# ── _extract_close_df ─────────────────────────────────────────────────────────


def test_extract_close_df_flattens_multi_index():
    idx = pd.date_range("2026-01-02", periods=3)
    raw = close_frame(idx, ["^NSEI"], [[1.0], [2.0], [3.0]])
    out = svc._extract_close_df(raw)
    assert list(out.columns) == ["^NSEI"]
    assert float(out["^NSEI"].iloc[-1]) == 3.0


def test_extract_close_df_handles_empty():
    assert svc._extract_close_df(None).empty
    assert svc._extract_close_df(pd.DataFrame()).empty


# ── history ───────────────────────────────────────────────────────────────────


def test_fetch_history_flattens_and_serializes(monkeypatch):
    idx = pd.date_range("2026-01-02", periods=2, freq="D")
    flat = pd.DataFrame(
        {
            "Open": [10.0, 11.0],
            "High": [12.0, 13.0],
            "Low": [9.0, 10.5],
            "Close": [11.0, 12.5],
            "Volume": [1000, 2000],
        },
        index=idx,
    )
    raw = ohlcv_with_yf_columns(flat, "RELIANCE.NS")

    monkeypatch.setattr(svc.yf, "download", lambda *a, **k: raw)
    candles = svc._fetch_history("RELIANCE.NS", "1d", "2y")
    assert len(candles) == 2
    first = candles[0]
    assert first["open"] == 10.0 and first["close"] == 11.0
    assert first["volume"] == 1000
    assert first["time"].startswith(idx[0].isoformat()[:10])


def test_fetch_history_nan_volume_maps_to_none(monkeypatch):
    idx = pd.date_range("2026-01-02", periods=1)
    flat = pd.DataFrame(
        {
            "Open": [10.0],
            "High": [12.0],
            "Low": [9.0],
            "Close": [11.0],
            "Volume": [float("nan")],
        },
        index=idx,
    )
    monkeypatch.setattr(
        svc.yf, "download", lambda *a, **k: ohlcv_with_yf_columns(flat, "X.NS")
    )
    candles = svc._fetch_history("X.NS", "1d", "2y")
    assert candles[0]["volume"] is None


def test_fetch_history_empty_raises_404(monkeypatch):
    monkeypatch.setattr(svc.yf, "download", lambda *a, **k: pd.DataFrame())
    with pytest.raises(HTTPException) as exc:
        svc._fetch_history("BOGUS.NS", "1d", "2y")
    assert exc.value.status_code == 404


def test_fetch_history_upstream_error_raises_502(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("yahoo down")

    monkeypatch.setattr(svc.yf, "download", boom)
    with pytest.raises(HTTPException) as exc:
        svc._fetch_history("RELIANCE.NS", "1d", "2y")
    assert exc.value.status_code == 502


# ── quote ─────────────────────────────────────────────────────────────────────


class FakeFastInfo:
    def __init__(self, last, prev):
        self._last = last
        self._prev = prev

    @property
    def last_price(self):
        return self._last

    @property
    def previous_close(self):
        return self._prev


class FakeTicker:
    def __init__(self, last, prev):
        self.fast_info = FakeFastInfo(last, prev)


def test_fetch_quote_fast_info_path(monkeypatch):
    monkeypatch.setattr(svc.yf, "Ticker", lambda sym: FakeTicker(2984.5, 2950.0))
    data = svc._fetch_quote("RELIANCE.NS")
    assert data["price"] == 2984.5
    assert data["previous_close"] == 2950.0
    assert data["change"] == pytest.approx(34.5)
    assert data["change_pct"] == pytest.approx(34.5 / 2950.0 * 100)


def test_fetch_quote_history_fallback(monkeypatch):
    idx = pd.date_range("2026-08-20 09:15", periods=2, freq="1min")
    hist = pd.DataFrame({"Close": [100.0, 101.5]}, index=idx)

    class FallbackTicker:
        fast_info = FakeFastInfo(None, None)

        def history(self, *a, **k):
            return hist

    monkeypatch.setattr(svc.yf, "Ticker", lambda sym: FallbackTicker())
    data = svc._fetch_quote("TCS.NS")
    assert data["price"] == 101.5
    assert data["previous_close"] == 100.0


def test_fetch_quote_no_price_raises_404(monkeypatch):
    class EmptyTicker:
        fast_info = FakeFastInfo(None, None)

        def history(self, *a, **k):
            return pd.DataFrame()

    monkeypatch.setattr(svc.yf, "Ticker", lambda sym: EmptyTicker())
    with pytest.raises(HTTPException) as exc:
        svc._fetch_quote("DEAD.NS")
    assert exc.value.status_code == 404


def test_fetch_quote_upstream_error_raises_502(monkeypatch):
    class ExplodingTicker:
        @property
        def fast_info(self):
            raise RuntimeError("network gone")

    monkeypatch.setattr(svc.yf, "Ticker", lambda sym: ExplodingTicker())
    with pytest.raises(HTTPException) as exc:
        svc._fetch_quote("RELIANCE.NS")
    assert exc.value.status_code == 502


# ── movers ────────────────────────────────────────────────────────────────────


def test_fetch_gainers_losers_orders_top5(monkeypatch):
    # Engineered so % changes are distinct: prev close 100 -> live 85..145.
    syms = [f"S{i}.NS" for i in range(7)]
    live_by_sym = {sym: 80.0 + i * 10.0 + 5.0 for i, sym in enumerate(reversed(syms))}
    dates = pd.date_range("2026-01-01", periods=3)
    daily_rows = [[100.0] * len(syms) for _ in range(3)]

    calls = {"n": 0}

    def fake_download(tickers, **kwargs):
        calls["n"] += 1
        if kwargs.get("interval") == "1d":
            return close_frame(dates, tickers, daily_rows)
        return close_frame([dates[-1]], tickers,
                           [[live_by_sym[sym] for sym in tickers]])

    monkeypatch.setattr(svc, "MOVERS_TICKERS", syms)
    monkeypatch.setattr(svc.yf, "download", fake_download)
    result = svc._fetch_gainers_losers()

    assert calls["n"] == 2
    # % change desc: S0(+45) S1(+35) S2(+25) S3(+15) S4(+5) S5(-5) S6(-15);
    # losers = tail(5) of the desc sort re-sorted ascending.
    assert [g["symbol"] for g in result["gainers"]] == [
        "S0", "S1", "S2", "S3", "S4"
    ]
    assert [l["symbol"] for l in result["losers"]] == [
        "S6", "S5", "S4", "S3", "S2"
    ]
    top = result["gainers"][0]
    assert top["change_pct"] == pytest.approx(45.0)
    assert math.isfinite(top["price"])
