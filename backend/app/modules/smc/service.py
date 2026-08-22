from __future__ import annotations

from typing import Any

import anyio.to_thread
import numpy as np
import pandas as pd

from app.modules.analytics.service import candles_to_df
from app.modules.market_data import service as market_data

# ── TraderBuddies SMC engine (verbatim port of app.py:1925-2136) ─────────────
# Python translation of the TraderBuddies Pine Script indicator.
# Computes: swing highs/lows, BOS/CHoCH market structure,
# Order Blocks, Fair Value Gaps, Premium/Discount zones.


def _pivot_highs(arr: np.ndarray, length: int, n: int) -> np.ndarray:
    ph = np.full(n, np.nan)
    for i in range(length, n - length):
        window = arr[i - length : i + length + 1]
        if arr[i] == np.max(window):
            ph[i] = arr[i]
    return ph


def _pivot_lows(arr: np.ndarray, length: int, n: int) -> np.ndarray:
    pl = np.full(n, np.nan)
    for i in range(length, n - length):
        window = arr[i - length : i + length + 1]
        if arr[i] == np.min(window):
            pl[i] = arr[i]
    return pl


def compute_traderbuddies(
    df: pd.DataFrame,
    swing_len: int = 50,
    int_len: int = 5,
    ob_count: int = 3,
) -> dict[str, Any]:
    hi = df["High"].values
    lo = df["Low"].values
    cl = df["Close"].values
    op = df["Open"].values
    n = len(df)

    # ── Swing High / Low detection ────────────────────────────────
    swing_highs = _pivot_highs(hi, swing_len, n)
    swing_lows = _pivot_lows(lo, swing_len, n)
    int_highs = _pivot_highs(hi, int_len, n)
    int_lows = _pivot_lows(lo, int_len, n)

    # ── Market Structure (BOS / CHoCH) — internal ─────────────────
    ms_signals: list[dict] = []  # {idx, price, label, bull}
    itrend = 0
    last_iH: tuple[int, float] | None = None
    last_iL: tuple[int, float] | None = None
    prev_iL_price: float | None = None
    prev_iH_price: float | None = None

    for i in range(int_len, n):
        if not np.isnan(int_highs[i]):
            prev_iH_price = last_iH[1] if last_iH else None
            last_iH = (i, float(int_highs[i]))
        if not np.isnan(int_lows[i]):
            prev_iL_price = last_iL[1] if last_iL else None
            last_iL = (i, float(int_lows[i]))

        if last_iH and last_iL:
            # Bullish break
            if cl[i] > last_iH[1]:
                if itrend < 0:
                    lbl = (
                        "CHoCH+"
                        if (prev_iL_price and last_iL[1] > prev_iL_price)
                        else "CHoCH"
                    )
                else:
                    lbl = "BOS"
                ms_signals.append(
                    {"idx": last_iH[0], "price": last_iH[1], "label": lbl, "bull": True}
                )
                itrend = 1
                last_iH = None
            # Bearish break
            elif cl[i] < last_iL[1]:
                if itrend > 0:
                    lbl = (
                        "CHoCH+"
                        if (prev_iH_price and last_iH and last_iH[1] < prev_iH_price)
                        else "CHoCH"
                    )
                else:
                    lbl = "BOS"
                ms_signals.append(
                    {"idx": last_iL[0], "price": last_iL[1], "label": lbl, "bull": False}
                )
                itrend = -1
                last_iL = None

    # Market Structure — swing
    swing_ms: list[dict] = []
    strend = 0
    last_sH: tuple[int, float] | None = None
    last_sL: tuple[int, float] | None = None
    prev_sL_price: float | None = None
    prev_sH_price: float | None = None

    for i in range(swing_len, n):
        if not np.isnan(swing_highs[i]):
            prev_sH_price = last_sH[1] if last_sH else None
            last_sH = (i, float(swing_highs[i]))
        if not np.isnan(swing_lows[i]):
            prev_sL_price = last_sL[1] if last_sL else None
            last_sL = (i, float(swing_lows[i]))

        if last_sH and last_sL:
            if cl[i] > last_sH[1]:
                if strend < 0:
                    lbl = (
                        "CHoCH+"
                        if (prev_sL_price and last_sL[1] > prev_sL_price)
                        else "CHoCH"
                    )
                else:
                    lbl = "BOS"
                swing_ms.append(
                    {"idx": last_sH[0], "price": last_sH[1], "label": lbl, "bull": True}
                )
                strend = 1
                last_sH = None
            elif cl[i] < last_sL[1]:
                if strend > 0:
                    lbl = (
                        "CHoCH+"
                        if (prev_sH_price and last_sH and last_sH[1] < prev_sH_price)
                        else "CHoCH"
                    )
                else:
                    lbl = "BOS"
                swing_ms.append(
                    {"idx": last_sL[0], "price": last_sL[1], "label": lbl, "bull": False}
                )
                strend = -1
                last_sL = None

    # ── Order Blocks ──────────────────────────────────────────────
    # Last opposing candle before a structural break.
    bull_obs: list[dict] = []
    bear_obs: list[dict] = []

    all_ms = sorted(ms_signals + swing_ms, key=lambda x: x["idx"])
    seen: set[int] = set()
    for sig in all_ms[-ob_count * 2 :]:
        si = sig["idx"]
        if si in seen:
            continue
        seen.add(si)
        if sig["bull"]:
            # Look back from signal for last bearish (red) candle
            for j in range(si, max(si - 20, 0), -1):
                if cl[j] < op[j]:
                    top = max(op[j], cl[j])
                    btm = min(op[j], cl[j])
                    bull_obs.append(
                        {"top": float(top), "btm": float(btm), "idx": j}
                    )
                    break
        else:
            # Look back for last bullish (green) candle
            for j in range(si, max(si - 20, 0), -1):
                if cl[j] > op[j]:
                    top = max(op[j], cl[j])
                    btm = min(op[j], cl[j])
                    bear_obs.append(
                        {"top": float(top), "btm": float(btm), "idx": j}
                    )
                    break

    # Mark mitigated OBs (price re-entered the OB zone)
    last_close = cl[-1]
    for ob in bull_obs:
        ob["mitigated"] = bool(last_close < ob["top"])
    for ob in bear_obs:
        ob["mitigated"] = bool(last_close > ob["btm"])

    bull_obs = sorted(bull_obs, key=lambda x: x["idx"])[-ob_count:]
    bear_obs = sorted(bear_obs, key=lambda x: x["idx"])[-ob_count:]

    # ── Fair Value Gaps ───────────────────────────────────────────
    fvgs: list[dict] = []
    fvg_limit = 5
    bull_fvg_count = bear_fvg_count = 0
    for i in range(2, n):
        if lo[i] > hi[i - 2] and bull_fvg_count < fvg_limit:
            fvgs.append(
                {
                    "bull": True,
                    "top": float(lo[i]),
                    "btm": float(hi[i - 2]),
                    "idx": i,
                    "mitigated": bool(cl[-1] < lo[i]),
                }
            )
            bull_fvg_count += 1
        elif hi[i] < lo[i - 2] and bear_fvg_count < fvg_limit:
            fvgs.append(
                {
                    "bull": False,
                    "top": float(lo[i - 2]),
                    "btm": float(hi[i]),
                    "idx": i,
                    "mitigated": bool(cl[-1] > lo[i - 2]),
                }
            )
            bear_fvg_count += 1

    fvgs = [f for f in fvgs][-6:]  # most recent overall (3 bull + 3 bear)

    # ── Premium / Discount / Equilibrium ──────────────────────────
    range_high: float | None
    range_low: float | None
    equilibrium: float | None
    valid_sh = [hi[i] for i in range(n) if not np.isnan(swing_highs[i])]
    valid_sl = [lo[i] for i in range(n) if not np.isnan(swing_lows[i])]
    if valid_sh and valid_sl:
        range_high = float(max(valid_sh[-3:]) if len(valid_sh) >= 3 else max(valid_sh))
        range_low = float(min(valid_sl[-3:]) if len(valid_sl) >= 3 else min(valid_sl))
        equilibrium = (range_high + range_low) / 2
    else:
        range_high = range_low = equilibrium = None

    return {
        "swing_highs": swing_highs,
        "swing_lows": swing_lows,
        "ms_signals": ms_signals[-20:],
        "bull_obs": bull_obs,
        "bear_obs": bear_obs,
        "fvgs": fvgs,
        "range_high": range_high,
        "range_low": range_low,
        "equilibrium": equilibrium,
        "itrend": itrend,
        "strend": strend,
    }


# ── Async API: JSON-shaped wrapper around the verbatim engine ────────────────


def _points(index: pd.DatetimeIndex, values: np.ndarray) -> list[dict]:
    """Non-NaN pivot values -> [{time, value}] for chart overlays."""
    return [
        {"time": index[i].isoformat(), "value": float(v)}
        for i, v in enumerate(values)
        if not np.isnan(v)
    ]


async def get_smc(
    symbol: str,
    interval,
    period,
    swing_len: int = 50,
    int_len: int = 5,
    ob_count: int = 3,
) -> dict:
    candles = await market_data.get_history(symbol, interval, period)

    def compute() -> dict:
        df = candles_to_df(candles)

        # Guard identical to app.py:2140 — engine needs enough bars.
        if len(df) < max(swing_len * 2 + 1, 20):
            return {
                "swing_highs": [], "swing_lows": [], "ms_signals": [],
                "bull_obs": [], "bear_obs": [], "fvgs": [],
                "range_high": None, "range_low": None, "equilibrium": None,
                "itrend": 0, "strend": 0,
            }

        raw = compute_traderbuddies(df, swing_len, int_len, ob_count)
        index = df.index

        def box(b: dict) -> dict:
            return {
                "time": index[b["idx"]].isoformat(),
                "top": b["top"],
                "btm": b["btm"],
                "mitigated": b["mitigated"],
            }

        return {
            "swing_highs": _points(index, raw["swing_highs"]),
            "swing_lows": _points(index, raw["swing_lows"]),
            "ms_signals": [
                {
                    "time": index[s["idx"]].isoformat(),
                    "price": s["price"],
                    "label": s["label"],
                    "bull": s["bull"],
                }
                for s in raw["ms_signals"]
            ],
            "bull_obs": [box(b) for b in raw["bull_obs"]],
            "bear_obs": [box(b) for b in raw["bear_obs"]],
            "fvgs": [
                {
                    "time": index[f["idx"]].isoformat(),
                    "bull": f["bull"],
                    "top": f["top"],
                    "btm": f["btm"],
                    "mitigated": f["mitigated"],
                }
                for f in raw["fvgs"]
            ],
            "range_high": raw["range_high"],
            "range_low": raw["range_low"],
            "equilibrium": raw["equilibrium"],
            "itrend": raw["itrend"],
            "strend": raw["strend"],
        }

    return await anyio.to_thread.run_sync(compute)
