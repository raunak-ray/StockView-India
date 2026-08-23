from __future__ import annotations

import typing

import pandas as pd
import pytest

from app.modules.market_data import service as md_service
from app.modules.nse import service as nse_service

# ── PCR / Max Pain ────────────────────────────────────────────────────────────


def _chain(strikes, ce_oi, pe_oi) -> dict:
    return {
        "records": {
            "data": [
                {"strikePrice": k,
                 "CE": {"openInterest": c},
                 "PE": {"openInterest": p}}
                for k, c, p in zip(strikes, ce_oi, pe_oi)
            ]
        }
    }


def test_compute_pcr_maxpain_engineered_chain():
    # 3-strike chain: PCR = 90/30 = 3.0; min total payout sits at strike 100.
    oc = _chain([100, 110, 120], [10, 10, 10], [30, 30, 30])
    pcr, max_pain = nse_service.compute_pcr_maxpain(oc)
    assert pcr == pytest.approx(3.0)
    assert max_pain == pytest.approx(100.0)


def test_compute_pcr_maxpain_empty_chain():
    assert nse_service.compute_pcr_maxpain({}) == (None, None)


def test_compute_pcr_maxpain_zero_ce_oi():
    oc = _chain([100], [0], [10])
    pcr, _ = nse_service.compute_pcr_maxpain(oc)
    assert pcr is None


# ── FII / DII helpers ─────────────────────────────────────────────────────────


def test_safe_float_variants():
    f = nse_service._safe_float
    assert f("1,234.56") == 1234.56
    assert f("−500") == -500.0  # unicode minus from scrapes
    assert f("") == 0.0
    assert f("garbage") == 0.0


def test_rows_from_api_items_normalises():
    rows = nse_service._rows_from_api_items(
        [{"date": "01-Jan-2026", "fiiBuy": "100", "fiiSell": "80",
          "fiiNet": "20", "diiBuy": "50", "diiSell": "60", "diiNet": "-10"}]
    )
    assert rows[0]["Date"] == "01-Jan-2026"
    assert rows[0]["FII Net"] == 20.0
    assert rows[0]["DII Net"] == -10.0
    assert len(nse_service._STATIC_FII_DII) == 10  # static fallback intact


# ── Quote fallback normalisation (attempt 3: yfinance fast_info) ─────────────


class _FakeFastInfo:
    last_price = 2984.5
    previous_close = 2950.0
    open = 2960.0
    day_high = 3012.0
    day_low = 2951.0
    year_high = 3150.0
    year_low = 2310.0
    three_month_average_volume = 4200000
    regularMarketPrice = None


class _FakeTicker:
    fast_info = _FakeFastInfo()
    info: typing.ClassVar[dict] = {
        "longName": "Reliance Industries Ltd",
        "industry": "Energy",
    }


def test_nse_quote_yfinance_fallback_shape(monkeypatch):
    import yfinance as yf

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    raw = nse_service._fetch_nse_quote("RELIANCE")
    assert raw["priceInfo"]["lastPrice"] == 2984.5
    assert raw["priceInfo"]["pChange"] == pytest.approx((2984.5 - 2950.0) / 2950.0 * 100)
    assert raw["metadata"]["companyName"] == "Reliance Industries Ltd"
    assert raw["priceVolumeBlockData"]["totalTradedVolume"] == 4200000


# ── Sector performance (row 26) ───────────────────────────────────────────────


def test_sector_performance_groups_and_averages(monkeypatch):
    sectors = {
        "IT": [("TCS.NS", "TCS", 100)],
        "Oil & Gas": [("ONGC.NS", "ONGC", 50)],
    }
    monkeypatch.setattr(
        "app.modules.instruments.service.nifty50_sectors", lambda: sectors
    )

    def fake_download(tickers, **kwargs):
        idx = pd.date_range("2026-08-18", periods=2)
        data = {"TCS.NS": [100.0, 110.0], "ONGC.NS": [200.0, 190.0]}
        return pd.DataFrame(data, index=idx)

    import yfinance as yf

    monkeypatch.setattr(yf, "download", fake_download)

    out = md_service._sector_performance_impl()
    by_name = {s["name"]: s for s in out["sectors"]}
    assert by_name["IT"]["change_pct"] == pytest.approx(10.0)
    assert by_name["Oil & Gas"]["change_pct"] == pytest.approx(-5.0)
    tcs = by_name["IT"]["stocks"][0]
    assert (tcs["ticker"], tcs["label"], tcs["mcap"]) == ("TCS.NS", "TCS", 100)


def test_sector_performance_raises_when_feed_dead(monkeypatch):
    import yfinance as yf

    monkeypatch.setattr(yf, "download", lambda *a, **k: pd.DataFrame())
    with pytest.raises(md_service.HTTPException) as exc:
        md_service._sector_performance_impl()
    assert exc.value.status_code == 502
