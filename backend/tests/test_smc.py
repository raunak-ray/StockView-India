from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.modules.smc.service import (
    _points,
    compute_traderbuddies,
)


def smc_df() -> pd.DataFrame:
    """Uptrend + sine oscillation — creates genuine swings, breaks and OBs."""
    n = 80
    idx = pd.date_range("2026-01-01", periods=n, freq="D")
    trend = np.linspace(100, 150, n)
    wave = np.sin(np.linspace(0, 8 * np.pi, n)) * 4  # 4 full cycles
    close = trend + wave
    # Open at previous close so pullback candles are naturally red.
    open_ = np.concatenate([[close[0]], close[:-1]])
    return pd.DataFrame(
        {
            "Open": open_,
            "High": np.maximum(open_, close) + 0.8,
            "Low": np.minimum(open_, close) - 0.8,
            "Close": close,
            "Volume": np.full(n, 5000.0),
        },
        index=idx,
    )


SWING = 8
INT = 5


def test_bullish_structure_break_detected():
    out = compute_traderbuddies(smc_df(), swing_len=SWING, int_len=INT, ob_count=3)
    assert any(s["bull"] for s in out["ms_signals"])
    assert all(s["label"] in ("BOS", "CHoCH", "CHoCH+") for s in out["ms_signals"])
    assert out["itrend"] in (-1, 1)


def test_order_blocks_have_valid_bounds():
    out = compute_traderbuddies(smc_df(), swing_len=SWING, int_len=INT, ob_count=3)
    assert len(out["bull_obs"]) >= 1
    for ob in out["bull_obs"] + out["bear_obs"]:
        assert ob["top"] >= ob["btm"]
        assert isinstance(ob["mitigated"], bool)


def test_fvg_gap_detected():
    idx = pd.date_range("2026-01-01", periods=30, freq="D")
    close = np.full(30, 100.0)
    high = close + 0.5
    low = close - 0.5
    # Create a gap: low[15] jumps far above high[13]
    low[15] = 105.0
    df = pd.DataFrame(
        {
            "Open": close, "High": high, "Low": low,
            "Close": close, "Volume": np.full(30, 100.0),
        },
        index=idx,
    )
    out = compute_traderbuddies(df, swing_len=8, int_len=3, ob_count=2)
    assert any(f["bull"] for f in out["fvgs"])
    bull_fvgs = [f for f in out["fvgs"] if f["bull"]]
    assert bull_fvgs[-1]["btm"] == pytest.approx(100.5)  # hi[i-2]
    assert bull_fvgs[-1]["top"] == pytest.approx(105.0)  # lo[i]


def test_premium_discount_range_from_swings():
    out = compute_traderbuddies(smc_df(), swing_len=SWING, int_len=INT, ob_count=3)
    assert out["range_high"] is not None
    assert out["range_low"] is not None
    assert out["range_low"] < out["equilibrium"] < out["range_high"]
    assert out["strend"] in (-1, 0, 1)


def test_points_drops_nan_and_serializes():
    idx = pd.date_range("2026-02-01", periods=4, freq="D")
    values = np.array([np.nan, 10.0, np.nan, 12.0])
    pts = _points(idx, values)
    assert [p["value"] for p in pts] == [10.0, 12.0]
    assert pts[0]["time"].startswith("2026-02-02")


def test_engine_runs_on_tiny_frame_without_crash():
    tiny = smc_df().iloc[:8]
    out = compute_traderbuddies(tiny, swing_len=3, int_len=2, ob_count=1)
    assert isinstance(out["ms_signals"], list)
