from __future__ import annotations

import logging
import math
from typing import Any, Literal

import anyio.to_thread
import pandas as pd
import yfinance as yf
from fastapi import HTTPException, status

from app.core.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

# ── Cache TTLs (parity with st.cache_data decorators in app.py) ──────────────
HISTORY_TTL = 300  # load_df app.py:1034
INFO_TTL = 600  # load_info app.py:1047
QUOTE_TTL = 30  # fetch_live_price app.py:1054
SUMMARY_TTL = 60  # load_market_summary app.py:1071 (inner decorator governs)
MOVERS_TTL = 60  # load_gainers_losers app.py:1159

Interval = Literal["1d", "1wk", "1mo"]
Period = Literal["2y", "5y", "10y"]

# Major indices tracked on the dashboard (parity app.py:1081-1087).
INDICES: dict[str, str] = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Gold": "GC=F",
}

# NSE large-cap universe for the movers panel (parity app.py:1167-1173).
MOVERS_TICKERS: list[str] = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "WIPRO.NS",
    "SBIN.NS", "ICICIBANK.NS", "BAJFINANCE.NS", "TATAMOTORS.NS",
    "ADANIPORTS.NS", "MARUTI.NS", "HINDUNILVR.NS", "ASIANPAINT.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "ONGC.NS", "LT.NS", "ITC.NS",
    "SUNPHARMA.NS", "ZOMATO.NS",
]


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _upstream(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY, detail=detail
    )


def _finite(value: Any) -> float | None:
    """float() that maps NaN/inf (common in yfinance output) to None."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


# ══════════════════════════════════════════════════════════════════════════════
# Sync implementations (run in the threadpool — yfinance is blocking)
# ══════════════════════════════════════════════════════════════════════════════


def _extract_close_df(raw: pd.DataFrame | None) -> pd.DataFrame:
    """Flat Close frame from a possibly-MultiIndex download result.

    Parity with _extract_close_df/_close_df inner helpers (app.py:1091, 1175).
    """
    if raw is None or raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex) and "Close" in raw.columns.get_level_values(0):
        return raw["Close"]
    return pd.DataFrame()


def _fetch_history(symbol: str, interval: Interval, period: Period) -> list[dict]:
    """OHLCV rows. Ported from load_df (app.py:1035-1045), unchanged math."""
    try:
        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True,
        )
    except Exception as exc:
        raise _upstream(f"Yahoo Finance history failed: {exc}") from exc

    if df is None or df.empty:
        raise _not_found(f"No data found for '{symbol}'.")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].squeeze(), errors="coerce")
    df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)

    candles: list[dict] = []
    for timestamp, row in df.iterrows():
        volume = _finite(row.get("Volume"))
        candles.append(
            {
                "time": pd.Timestamp(timestamp).isoformat(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": volume,
            }
        )
    return candles


def _fetch_info(symbol: str) -> dict[str, Any]:
    """Ticker metadata. Ported from load_info (app.py:1048-1052)."""
    try:
        info = yf.Ticker(symbol).info
    except Exception as exc:
        raise _upstream(f"Yahoo Finance info failed: {exc}") from exc
    return info if isinstance(info, dict) else {}


def _fetch_quote(symbol: str) -> dict[str, Any]:
    """Last price vs previous close. Ported from fetch_live_price (app.py:1055-1068).

    Error taxonomy (plan/01 §8): unknown/no-data symbol -> 404, upstream
    transport failure -> 502.
    """
    try:
        tk = yf.Ticker(symbol)
    except Exception as exc:
        raise _upstream(f"Yahoo Finance quote unavailable: {exc}") from exc

    price: float | None = None
    prev: float | None = None
    try:
        fp = tk.fast_info
        last = getattr(fp, "last_price", None)
        previous = getattr(fp, "previous_close", None)
        if last is not None:
            price = float(last)
        if previous is not None:
            prev = float(previous)
    except Exception as exc:  # noqa: BLE001 - fall through to history fallback
        logger.debug("fast_info failed for %s: %s", symbol, exc)

    if price is None:
        try:
            hist = tk.history(period="2d", interval="1m", auto_adjust=True)
        except Exception as exc:
            raise _upstream(f"Yahoo Finance quote unavailable: {exc}") from exc
        if hist is None or hist.empty:
            raise _not_found(f"No live price found for '{symbol}'.")
        price = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price

    change = price - prev if prev is not None else None
    change_pct = (change / prev * 100) if (change is not None and prev) else None
    return {
        "price": price,
        "previous_close": prev,
        "change": _finite(change) if change is not None else None,
        "change_pct": _finite(change_pct) if change_pct is not None else None,
    }


def _fetch_market_summary() -> list[dict]:
    """Live index snapshot. Ported from load_market_summary (app.py:1072-1156).

    Strategy preserved exactly:
      Step 1: previous closes from 5d daily bars (second-to-last bar)
      Step 2: live prices from 1d 1-minute bars (latest tick)
      Step 3: per-ticker fast_info fallback
      Step 4: compute change vs previous close
    """
    syms = list(INDICES.values())
    prev_closes: dict[str, float] = {}
    live_prices: dict[str, float] = {}

    # Step 1: Previous closes (daily, last 5 days)
    try:
        raw_daily = yf.download(
            syms, period="5d", interval="1d", progress=False, auto_adjust=True
        )
        close_df = _extract_close_df(raw_daily)
        for sym in syms:
            if sym in close_df.columns:
                s = close_df[sym].dropna()
                if len(s) >= 2:
                    prev_closes[sym] = float(s.iloc[-2])
                elif len(s) == 1:
                    prev_closes[sym] = float(s.iloc[-1])
    except Exception as exc:  # noqa: BLE001 - graceful fallback chain
        logger.debug("market_data fallback step failed: %s", exc)

    # Step 2: Live price (1-minute bars, today)
    try:
        raw_live = yf.download(
            syms, period="1d", interval="1m", progress=False, auto_adjust=True
        )
        live_df = _extract_close_df(raw_live)
        for sym in syms:
            if sym in live_df.columns:
                s = live_df[sym].dropna()
                if not s.empty:
                    live_prices[sym] = float(s.iloc[-1])
    except Exception as exc:  # noqa: BLE001 - graceful fallback chain
        logger.debug("market_data fallback step failed: %s", exc)

    # Step 3: per-ticker fast_info fallback
    for sym in syms:
        if sym in live_prices and sym in prev_closes:
            continue
        try:
            fi = yf.Ticker(sym).fast_info
            lp = getattr(fi, "last_price", None) or getattr(
                fi, "regularMarketPrice", None
            )
            pc = getattr(fi, "previous_close", None) or getattr(
                fi, "regularMarketPreviousClose", None
            )
            if lp and sym not in live_prices:
                live_prices[sym] = float(lp)
            if pc and sym not in prev_closes:
                prev_closes[sym] = float(pc)
        except Exception as exc:  # noqa: BLE001 - graceful fallback chain
            logger.debug("fast_info fallback failed for %s: %s", sym, exc)

    # Step 4: Compute change and build results
    results: list[dict] = []
    for name, sym in INDICES.items():
        lp = live_prices.get(sym)
        pc = prev_closes.get(sym)
        if lp is None:
            continue
        if pc and pc > 0:
            chg = lp - pc
            pct = chg / pc * 100
            results.append(
                {"name": name, "symbol": sym, "price": lp,
                 "change": chg, "change_pct": pct}
            )
        else:
            results.append(
                {"name": name, "symbol": sym, "price": lp,
                 "change": 0.0, "change_pct": 0.0}
            )

    if not results:
        raise _upstream("Yahoo Finance index feed unavailable.")
    return results


def _fetch_gainers_losers() -> dict[str, list[dict]]:
    """Top movers. Ported from load_gainers_losers (app.py:1160-1225).

    Two-step live-vs-prev-close over MOVERS_TICKERS, then top 5 by % change.
    """
    prev_closes: dict[str, float] = {}
    live_prices: dict[str, float] = {}

    try:
        raw_d = yf.download(
            MOVERS_TICKERS, period="5d", interval="1d",
            progress=False, auto_adjust=True,
        )
        cdf = _extract_close_df(raw_d)
        for sym in MOVERS_TICKERS:
            if sym in cdf.columns:
                s = cdf[sym].dropna()
                if len(s) >= 2:
                    prev_closes[sym] = float(s.iloc[-2])
    except Exception as exc:  # noqa: BLE001 - graceful fallback chain
        logger.debug("market_data fallback step failed: %s", exc)

    try:
        raw_l = yf.download(
            MOVERS_TICKERS, period="1d", interval="1m",
            progress=False, auto_adjust=True,
        )
        ldf = _extract_close_df(raw_l)
        for sym in MOVERS_TICKERS:
            if sym in ldf.columns:
                s = ldf[sym].dropna()
                if not s.empty:
                    live_prices[sym] = float(s.iloc[-1])
    except Exception as exc:  # noqa: BLE001 - graceful fallback chain
        logger.debug("market_data fallback step failed: %s", exc)

    rows: list[dict] = []
    for sym in MOVERS_TICKERS:
        lp = live_prices.get(sym)
        pc = prev_closes.get(sym)
        if lp and pc and pc > 0:
            chg = lp - pc
            pct = chg / pc * 100
            rows.append(
                {"symbol": sym.replace(".NS", ""), "price": lp,
                 "change": chg, "change_pct": pct}
            )

    if not rows:
        raise _upstream("Yahoo Finance movers feed unavailable.")

    df = pd.DataFrame(rows).sort_values("change_pct", ascending=False)
    gainers = df.head(5).to_dict("records")
    losers = df.tail(5).sort_values("change_pct").to_dict("records")
    return {"gainers": gainers, "losers": losers}


# ══════════════════════════════════════════════════════════════════════════════
# Async API: Redis cache -> threadpool -> sync implementation
# ══════════════════════════════════════════════════════════════════════════════


async def _with_cache(key: str, ttl: int, func, *args) -> Any:
    cached = await cache_get(key)
    if cached is not None:
        return cached
    result = await anyio.to_thread.run_sync(func, *args)
    await cache_set(key, result, ttl)
    return result


async def get_history(symbol: str, interval: Interval, period: Period) -> list[dict]:
    return await _with_cache(
        f"md:history:{symbol}:{interval}:{period}", HISTORY_TTL,
        _fetch_history, symbol, interval, period,
    )


async def get_quote(symbol: str) -> dict[str, Any]:
    return await _with_cache(f"md:quote:{symbol}", QUOTE_TTL, _fetch_quote, symbol)


async def get_info(symbol: str) -> dict[str, Any]:
    return await _with_cache(f"md:info:{symbol}", INFO_TTL, _fetch_info, symbol)


async def get_market_summary() -> list[dict]:
    return await _with_cache("md:summary", SUMMARY_TTL, _fetch_market_summary)


async def get_gainers_losers() -> dict[str, list[dict]]:
    return await _with_cache("md:movers", MOVERS_TTL, _fetch_gainers_losers)
