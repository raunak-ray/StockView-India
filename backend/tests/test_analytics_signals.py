from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.modules.analytics.service import add_indicators, candles_to_df, find_sr
from app.modules.signals.service import compute_signal, generate_markers

# ── Fixtures ──────────────────────────────────────────────────────────────────


def ohlcv_df(n: int = 80, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    return pd.DataFrame(
        {
            "Open": close + rng.normal(0, 0.2, n),
            "High": close + np.abs(rng.normal(0.5, 0.2, n)),
            "Low": close - np.abs(rng.normal(0.5, 0.2, n)),
            "Close": close,
            "Volume": rng.integers(1_000, 10_000, n).astype(float),
        },
        index=pd.date_range("2026-01-01", periods=n, freq="D"),
    )


def enriched(n: int = 80) -> pd.DataFrame:
    return add_indicators(ohlcv_df(n))


# ── add_indicators ────────────────────────────────────────────────────────────


def test_add_indicators_matches_pandas_semantics():
    df = enriched()
    assert "SMA_20" in df and "EMA_20" in df and "RSI" in df and "MACD" in df
    manual_sma = df["Close"].rolling(20).mean().dropna().iloc[-1]
    assert df["SMA_20"].dropna().iloc[-1] == pytest.approx(manual_sma)
    rsi = df["RSI"].dropna()
    assert ((rsi >= 0) & (rsi <= 100)).all()


def test_add_indicators_respects_warmup_guards():
    short = add_indicators(ohlcv_df(15))
    assert "SMA_20" not in short.columns and "MACD" not in short.columns


def test_candles_to_df_shapes():
    candles = [
        {"time": "2026-01-02T00:00:00", "open": 1, "high": 2, "low": 0.5,
         "close": 1.5, "volume": 10},
    ]
    df = candles_to_df(candles)
    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert len(df) == 1


# ── find_sr ───────────────────────────────────────────────────────────────────


def test_find_sr_finds_clustered_levels():
    idx = pd.date_range("2026-01-01", periods=30, freq="D")
    base = np.full(30, 100.0)
    highs = base.copy()
    lows = base.copy()
    highs[5] = 110.0  # resistance peak
    lows[20] = 90.0  # support valley
    df = pd.DataFrame({"High": highs, "Low": lows}, index=idx)
    supports, resistances = find_sr(df, window=3, n_levels=3)
    assert any(abs(s - 90.0) < 1e-6 for s in supports)
    assert any(abs(r - 110.0) < 1e-6 for r in resistances)


# ── compute_signal (deterministic column control) ─────────────────────────────


def signal_frame(**columns) -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=25, freq="D")
    base = {"Close": np.linspace(100, 101, 25), "Volume": np.full(25, 1000.0)}
    base.update(columns)
    return pd.DataFrame(base, index=idx)


def test_compute_signal_strong_buy_branches():
    df = signal_frame()
    df["RSI"] = [np.nan] * 23 + [65.0, 65.0]  # >60 -> RSI Bullish buy (+1)
    df["MACD"] = [np.nan] * 23 + [-1.0, 1.0]  # cross up (+3)
    df["M_SIG"] = [np.nan] * 23 + [0.5, 0.5]
    df["SMA_20"] = [np.nan] * 23 + [98.0, 99.5]  # crosses above SMA50 (+4)
    df["SMA_50"] = [np.nan] * 23 + [99.0, 99.0]
    df["BB_H"] = [np.nan] * 24 + [200.0]
    df["BB_L"] = [np.nan] * 24 + [50.0]

    out = compute_signal(df)
    labels = {s["rule"] for s in out["signals"]}
    assert "Golden Cross 🌟" in labels and "MACD ↑ Cross" in labels
    assert out["score"] == 1 + 3 + 4
    assert out["verdict"] == "BUY"
    assert 50.0 <= out["confidence"] * 100 <= 100.0


def test_compute_signal_hold_when_all_neutral():
    df = signal_frame()
    df["RSI"] = [np.nan] * 24 + [50.0]  # neutral zone
    df["MACD"] = [np.nan] * 24 + [0.05]  # below signal -> bearish (-1)
    df["M_SIG"] = [np.nan] * 24 + [0.1]
    df["SMA_20"] = [np.nan] * 24 + [100.7]  # above SMA50 -> buy (+1)
    df["SMA_50"] = [np.nan] * 24 + [100.5]
    df["BB_H"] = [np.nan] * 24 + [102.0]
    df["BB_L"] = [np.nan] * 24 + [98.0]

    out = compute_signal(df)
    assert out["score"] == 0
    assert out["verdict"] == "HOLD"


def test_compute_signal_strong_sell():
    df = signal_frame()
    df["Close"] = np.full(25, 99.9)  # keep near-SMA20 and volume rules neutral
    df["RSI"] = [np.nan] * 23 + [80.0, 80.0]  # overbought (-2)
    df["MACD"] = [np.nan] * 23 + [1.0, -1.0]  # bearish cross (-3)
    df["M_SIG"] = [np.nan] * 23 + [0.0, 0.0]
    df["SMA_20"] = [np.nan] * 23 + [101.0, 99.0]  # death cross (-4)
    df["SMA_50"] = [np.nan] * 23 + [100.0, 100.0]
    df["BB_H"] = [np.nan] * 24 + [102.0]
    df["BB_L"] = [np.nan] * 24 + [98.0]

    out = compute_signal(df)
    assert out["score"] == -9
    assert out["verdict"] == "SELL"


# ── generate_markers ──────────────────────────────────────────────────────────


def test_generate_markers_on_macd_crossover():
    df = signal_frame(RSI=np.full(25, 50.0), MACD=np.zeros(25), M_SIG=np.zeros(25))
    df.iloc[-2, df.columns.get_loc("MACD")] = -1.0  # prev diff negative
    df.iloc[-1, df.columns.get_loc("MACD")] = 1.0  # curr diff positive

    markers = generate_markers(df)
    buys = [m for m in markers if m["kind"] == "buy"]
    assert len(buys) == 1
    expected_price = float(df["Close"].iloc[-1]) * 0.993
    assert buys[0]["price"] == pytest.approx(expected_price)
    assert buys[0]["position"] == "belowBar"
