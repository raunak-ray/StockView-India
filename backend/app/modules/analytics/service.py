from __future__ import annotations

import anyio.to_thread
import pandas as pd
import ta

from app.modules.market_data import service as market_data

# ── Indicator enrichment (verbatim port of app.py:1898-1920) ─────────────────
# VWAP omitted: our interval presets (1d/1wk/1mo) are never intraday, so the
# branch at app.py:1919 can never trigger.


def candles_to_df(candles: list[dict]) -> pd.DataFrame:
    """Candle dicts -> OHLCV frame indexed by timestamp."""
    df = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time")
    return df.rename(columns=str.title)[["Open", "High", "Low", "Close", "Volume"]]


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    if n > 20:
        df["SMA_20"] = df["Close"].rolling(20).mean()
        df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
        bb = ta.volatility.BollingerBands(close=df["Close"])
        df["BB_H"] = bb.bollinger_hband()
        df["BB_L"] = bb.bollinger_lband()
        df["BB_M"] = bb.bollinger_mavg()
    if n > 50:
        df["SMA_50"] = df["Close"].rolling(50).mean()
    if n > 14:
        df["RSI"] = ta.momentum.RSIIndicator(close=df["Close"]).rsi()
        df["ATR"] = ta.volatility.AverageTrueRange(
            high=df["High"], low=df["Low"], close=df["Close"]
        ).average_true_range()
    if n > 26:
        m = ta.trend.MACD(close=df["Close"])
        df["MACD"] = m.macd()
        df["M_SIG"] = m.macd_signal()
        df["M_HIS"] = m.macd_diff()
    return df


INDICATOR_COLUMNS = [
    "SMA_20", "SMA_50", "EMA_20", "BB_H", "BB_L", "BB_M",
    "RSI", "ATR", "MACD", "M_SIG", "M_HIS",
]


def _series(df: pd.DataFrame, column: str) -> list[dict]:
    s = df[column].dropna()
    return [{"time": ts.isoformat(), "value": float(v)} for ts, v in s.items()]


# ── Support / Resistance (verbatim port of app.py:2147-2165) ─────────────────


def find_sr(df: pd.DataFrame, window: int = 10, n_levels: int = 3):
    highs = df["High"].values
    lows = df["Low"].values
    rl, sl = [], []
    for i in range(window, len(df) - window):
        if highs[i] == max(highs[i - window : i + window + 1]):
            rl.append(highs[i])
        if lows[i] == min(lows[i - window : i + window + 1]):
            sl.append(lows[i])

    def cluster(lvls, tol=0.015):
        if not lvls:
            return []
        lvls = sorted(set(lvls))
        cls = [[lvls[0]]]
        for lv in lvls[1:]:
            if (lv - cls[-1][-1]) / cls[-1][-1] < tol:
                cls[-1].append(lv)
            else:
                cls.append([lv])
        return [float(pd.Series(c).mean()) for c in cls]

    return (
        sorted(cluster(sl))[:n_levels],
        sorted(cluster(rl), reverse=True)[:n_levels],
    )


# ── Async API (history comes Redis-cached from market_data) ──────────────────


async def get_indicators(symbol: str, interval, period) -> dict[str, list[dict]]:
    candles = await market_data.get_history(symbol, interval, period)

    def compute() -> dict[str, list[dict]]:
        df = add_indicators(candles_to_df(candles))
        return {
            column.lower(): _series(df, column)
            for column in INDICATOR_COLUMNS
            if column in df.columns
        }

    return await anyio.to_thread.run_sync(compute)


async def get_support_resistance(symbol: str, interval, period) -> dict:
    candles = await market_data.get_history(symbol, interval, period)

    def compute() -> dict:
        df = candles_to_df(candles)
        supports, resistances = find_sr(df)
        last_close = float(df["Close"].iloc[-1])
        return {
            "supports": supports,
            "resistances": resistances,
            "nearest_support": max(
                (s for s in supports if s < last_close), default=None
            ),
            "nearest_resistance": min(
                (r for r in resistances if r > last_close), default=None
            ),
        }

    return await anyio.to_thread.run_sync(compute)
