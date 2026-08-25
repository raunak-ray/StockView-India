"""Compare module — side-by-side multi-symbol comparison.

Provides snapshot data + normalised price overlay for 2-4 symbols.
Reuses market_data service; no new external dependencies.
"""

from __future__ import annotations

import logging

import pandas as pd

from app.modules.market_data import service as market_data
from app.modules.market_data.service import Period

logger = logging.getLogger(__name__)

_PERIOD_MAP: dict[str, Period] = {"1mo": "2y", "3mo": "2y", "6mo": "2y", "1y": "2y", "3y": "5y", "5y": "5y"}

_NAMES: dict[str, str] = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "HDFCBANK.NS": "HDFC Bank",
    "INFY.NS": "Infosys",
    "ICICIBANK.NS": "ICICI Bank",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "SBIN.NS": "State Bank of India",
    "BHARTIARTL.NS": "Bharti Airtel",
    "ITC.NS": "ITC",
    "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "LT.NS": "Larsen & Toubro",
    "AXISBANK.NS": "Axis Bank",
    "BAJFINANCE.NS": "Bajaj Finance",
    "MARUTI.NS": "Maruti Suzuki",
    "SUNPHARMA.NS": "Sun Pharma",
    "TATAMOTORS.NS": "Tata Motors",
    "WIPRO.NS": "Wipro",
    "HCLTECH.NS": "HCL Technologies",
    "TITAN.NS": "Titan Company",
    "ASIANPAINT.NS": "Asian Paints",
}


def _get_name(symbol: str) -> str:
    if symbol in _NAMES:
        return _NAMES[symbol]
    clean = symbol.replace(".NS", "").replace(".BO", "")
    return clean.replace("^", "").replace(".", " ").title()


def _build_snapshot(symbol: str, info: dict, df: pd.DataFrame | None) -> dict:
    last_price = float(info.get("currentPrice") or info.get("regularMarketPrice") or 0)
    change_pct = float(info.get("regularMarketChangePercent") or 0)
    volume = int(info.get("regularMarketVolume") or 0)
    market_cap = info.get("marketCap")
    pe_ratio = info.get("trailingPE")
    high_52w = info.get("fiftyTwoWeekHigh")
    low_52w = info.get("fiftyTwoWeekLow")

    sma_20 = sma_50 = rsi_val = macd_val = macd_sig = macd_hist = None

    if df is not None and len(df) >= 20:
        close = df["Close"]
        sma_20 = float(close.rolling(20).mean().iloc[-1])
        if len(df) >= 50:
            sma_50 = float(close.rolling(50).mean().iloc[-1])

        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, float("nan"))
        rsi_s = 100 - (100 / (1 + rs))
        rsi_drop = rsi_s.dropna()
        if len(rsi_drop) > 0:
            rsi_val = float(rsi_drop.iloc[-1])

        if len(df) >= 26:
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            sig_line = macd_line.ewm(span=9, adjust=False).mean()
            macd_val = float(macd_line.iloc[-1])
            macd_sig = float(sig_line.iloc[-1])
            macd_hist = float(macd_line.iloc[-1] - sig_line.iloc[-1])

    return {
        "symbol": symbol,
        "name": _get_name(symbol),
        "last_price": round(last_price, 2),
        "change_pct": round(change_pct, 2),
        "volume": volume,
        "market_cap": market_cap,
        "pe_ratio": round(pe_ratio, 2) if pe_ratio else None,
        "high_52w": round(high_52w, 2) if high_52w else None,
        "low_52w": round(low_52w, 2) if low_52w else None,
        "sma_20": round(sma_20, 2) if sma_20 else None,
        "sma_50": round(sma_50, 2) if sma_50 else None,
        "rsi": round(rsi_val, 1) if rsi_val is not None else None,
        "macd": round(macd_val, 2) if macd_val is not None else None,
        "macd_signal": round(macd_sig, 2) if macd_sig is not None else None,
        "macd_hist": round(macd_hist, 2) if macd_hist is not None else None,
    }


def _build_normalized(hist_map: dict[str, pd.DataFrame]) -> list[dict]:
    if not hist_map:
        return []

    all_dates = None
    for df in hist_map.values():
        dates = set(df.index.strftime("%Y-%m-%d"))
        all_dates = dates if all_dates is None else all_dates & dates
    if not all_dates:
        return []

    sorted_dates = sorted(all_dates)
    if len(sorted_dates) < 2:
        return []

    base_prices: dict[str, float] = {}
    for sym, df in hist_map.items():
        for d in sorted_dates:
            ts = pd.Timestamp(d)
            if ts in df.index:
                base_prices[sym] = float(df.loc[ts, "Close"])
                break
        else:
            base_prices[sym] = 1.0

    result = []
    for d in sorted_dates:
        ts = pd.Timestamp(d)
        vals = {}
        for sym, df in hist_map.items():
            if ts in df.index:
                raw = float(df.loc[ts, "Close"])
                vals[sym] = round((raw / base_prices[sym]) * 100, 2)
        if vals:
            result.append({"date": d, "values": vals})
    return result


async def compare_symbols(symbols: list[str], period: str = "1y") -> dict:
    clean_syms = [s.strip().upper() for s in symbols]
    yf_period: Period = _PERIOD_MAP.get(period, "2y")  # type: ignore[assignment]

    async def _fetch_one(sym: str) -> tuple[dict, pd.DataFrame | None]:
        try:
            info = await market_data.get_info(sym)
        except Exception:  # noqa: BLE001
            info = {}
        try:
            candles = await market_data.get_history(sym, "1d", yf_period)
            df = pd.DataFrame(candles)
            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"])
                df.set_index("time", inplace=True)
            for col in ["open", "high", "low", "close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            df.rename(
                columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"},
                inplace=True,
            )
        except Exception:  # noqa: BLE001
            df = None
        return info, df

    results = [await _fetch_one(s) for s in clean_syms]

    snapshots = []
    hist_map: dict[str, pd.DataFrame] = {}
    for sym, (info, df) in zip(clean_syms, results):
        snapshots.append(_build_snapshot(sym, info, df))
        if df is not None and "Close" in df.columns and len(df) > 10:
            hist_map[sym] = df

    normalized = _build_normalized(hist_map)

    return {
        "symbols": snapshots,
        "normalized": normalized,
        "period": period,
    }
