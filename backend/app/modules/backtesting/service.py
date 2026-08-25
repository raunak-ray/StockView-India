"""Backtesting service — verbatim port of app.py:5735-6067.

Engine: signal on bar[i] → fill at bar[i+1] Open (no look-ahead bias).
Slippage 0.05%, single-side commission, intrabar SL/TP.
6 strategies ported verbatim with identical thresholds.
"""

from __future__ import annotations

import anyio.to_thread
import numpy as np
import pandas as pd

from app.modules.market_data import service as market_data
from app.modules.market_data.service import Period

SLIPPAGE_PCT = 0.05

_PERIOD_MAP: dict[int, Period] = {1: "2y", 2: "2y", 3: "5y", 5: "5y", 7: "10y", 10: "10y"}

STRATEGIES = [
    "SMA Crossover",
    "RSI Mean Reversion",
    "MACD Crossover",
    "Bollinger Band Bounce",
    "EMA Trend",
    "Golden Cross (SMA50/200)",
]

STRATEGY_DESCRIPTIONS = {
    "SMA Crossover": "Buy when SMA20 crosses above SMA50. Sell on death cross. Classic trend-following.",
    "RSI Mean Reversion": "Buy when RSI < 35 (oversold). Sell when RSI > 65 (overbought). Counter-trend.",
    "MACD Crossover": "Buy on MACD bullish crossover (MACD > Signal). Sell on bearish crossover.",
    "Bollinger Band Bounce": "Buy when price touches lower Bollinger Band. Sell at upper band. Mean-reversion.",
    "EMA Trend": "Buy when EMA20 crosses above SMA50. Sell on reverse. Fast trend filter.",
    "Golden Cross (SMA50/200)": "Buy on Golden Cross (SMA50 > SMA200). Sell on Death Cross. Long-term signal.",
}


# ── Indicator computation (verbatim port of app.py:5748-5772) ───────────────


def _add_bt_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all indicators needed for backtesting strategies."""
    import ta

    d = df.copy()
    n = len(d)
    if n > 20:
        d["SMA20"] = d["Close"].rolling(20).mean()
        d["EMA20"] = d["Close"].ewm(span=20, adjust=False).mean()
        bb = ta.volatility.BollingerBands(close=d["Close"])
        d["BB_H"] = bb.bollinger_hband()
        d["BB_L"] = bb.bollinger_lband()
    if n > 50:
        d["SMA50"] = d["Close"].rolling(50).mean()
        d["SMA200"] = d["Close"].rolling(200).mean()
    if n > 14:
        d["RSI"] = ta.momentum.RSIIndicator(close=d["Close"]).rsi()
        d["ATR"] = ta.volatility.AverageTrueRange(
            high=d["High"], low=d["Low"], close=d["Close"]
        ).average_true_range()
    if n > 26:
        m = ta.trend.MACD(close=d["Close"])
        d["MACD"] = m.macd()
        d["MACD_S"] = m.macd_signal()
    if n > 12:
        d["EMA12"] = d["Close"].ewm(span=12, adjust=False).mean()
        d["EMA26"] = d["Close"].ewm(span=26, adjust=False).mean()
    return d


# ── Core engine (verbatim port of app.py:5774-6067) ─────────────────────────


def _run_backtest_sync(
    df: pd.DataFrame,
    strategy: str,
    initial_capital: float,
    commission_pct: float,
    sl_pct: float,
    tp_pct: float,
    position_size_pct: float,
) -> dict:
    if df.empty or len(df) < 60:
        return {}

    d = _add_bt_indicators(df)
    d = d.dropna().reset_index()

    capital = initial_capital
    position = 0.0
    entry_px = 0.0
    entry_date = None
    sl_price = 0.0
    tp_price = 0.0
    pending_entry = False
    pending_exit = False

    equity_curve = []
    trades = []

    def entry_signal(i: int) -> bool:
        if i < 1:
            return False
        row = d.iloc[i]
        prev = d.iloc[i - 1]
        if strategy == "SMA Crossover":
            return (prev["SMA20"] < prev["SMA50"]) and (row["SMA20"] > row["SMA50"])
        elif strategy == "RSI Mean Reversion":
            return row["RSI"] < 35
        elif strategy == "MACD Crossover":
            return (prev["MACD"] < prev["MACD_S"]) and (row["MACD"] > row["MACD_S"])
        elif strategy == "Bollinger Band Bounce":
            return row["Close"] < row["BB_L"]
        elif strategy == "EMA Trend":
            return (prev["EMA20"] < prev["SMA50"]) and (row["EMA20"] > row["SMA50"])
        elif strategy == "Golden Cross (SMA50/200)":
            if "SMA200" not in d.columns:
                return False
            return (prev["SMA50"] < prev["SMA200"]) and (row["SMA50"] > row["SMA200"])
        return False

    def exit_signal(i: int) -> bool:
        if i < 1:
            return False
        row = d.iloc[i]
        prev = d.iloc[i - 1]
        if strategy == "SMA Crossover":
            return (prev["SMA20"] > prev["SMA50"]) and (row["SMA20"] < row["SMA50"])
        elif strategy == "RSI Mean Reversion":
            return row["RSI"] > 65
        elif strategy == "MACD Crossover":
            return (prev["MACD"] > prev["MACD_S"]) and (row["MACD"] < row["MACD_S"])
        elif strategy == "Bollinger Band Bounce":
            return row["Close"] > row["BB_H"]
        elif strategy == "EMA Trend":
            return (prev["EMA20"] > prev["SMA50"]) and (row["EMA20"] < row["SMA50"])
        elif strategy == "Golden Cross (SMA50/200)":
            if "SMA200" not in d.columns:
                return False
            return (prev["SMA50"] > prev["SMA200"]) and (row["SMA50"] < row["SMA200"])
        return False

    def _close_trade(fill_px: float, date, exit_reason: str):
        nonlocal capital, position, entry_px, entry_date, sl_price, tp_price, pending_exit
        gross = position * fill_px
        commission_paid = gross * (commission_pct / 100.0)
        net = gross - commission_paid
        capital += net
        pnl = net - (position * entry_px)
        pnl_pct = (fill_px - entry_px) / entry_px * 100.0
        hold_days = 0
        try:
            hold_days = (pd.Timestamp(date) - pd.Timestamp(entry_date)).days
        except (ValueError, TypeError):
            pass
        trades.append({
            "entry_date": str(entry_date)[:10],
            "exit_date": str(date)[:10],
            "entry_px": round(entry_px, 2),
            "exit_px": round(fill_px, 2),
            "shares": round(position, 4),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "hold_days": hold_days,
            "exit_reason": exit_reason,
            "win": pnl > 0,
        })
        position = 0.0
        entry_px = 0.0
        sl_price = 0.0
        tp_price = float("inf")
        pending_exit = False

    for i in range(len(d)):
        row = d.iloc[i]
        date = row.get("Date", row.get("index", i))
        open_ = float(row["Open"])
        close = float(row["Close"])
        low = float(row["Low"])
        high = float(row["High"])

        # Execute PENDING ENTRY at today's Open
        if pending_entry and position == 0.0:
            fill_px = open_ * (1 + SLIPPAGE_PCT / 100.0)
            invest = capital * (position_size_pct / 100.0)
            invest = min(invest, capital)
            commission_paid = invest * (commission_pct / 100.0)
            net_invest = invest - commission_paid
            shares = net_invest / fill_px
            capital -= invest
            position = shares
            entry_px = fill_px
            entry_date = date
            sl_price = entry_px * (1 - sl_pct / 100.0) if sl_pct > 0 else 0.0
            tp_price = entry_px * (1 + tp_pct / 100.0) if tp_pct > 0 else float("inf")
            pending_entry = False

        # Execute PENDING EXIT at today's Open
        elif pending_exit and position > 0.0:
            fill_px = open_ * (1 - SLIPPAGE_PCT / 100.0)
            _close_trade(fill_px, date, "Signal")

        # Intrabar SL / TP
        if position > 0.0:
            if sl_price > 0 and low <= sl_price:
                fill_px = sl_price * (1 - SLIPPAGE_PCT / 100.0)
                _close_trade(fill_px, date, "SL")
            elif tp_price < float("inf") and high >= tp_price:
                fill_px = tp_price * (1 - SLIPPAGE_PCT / 100.0)
                _close_trade(fill_px, date, "TP")

        # Detect signal on THIS bar → execute on NEXT bar open
        if position == 0.0 and not pending_entry and entry_signal(i):
            pending_entry = True
        elif position > 0.0 and not pending_exit and exit_signal(i):
            pending_exit = True

        equity_curve.append({"date": str(date)[:10], "equity": round(capital + position * close, 2)})

    # Close any open position at last bar
    if position > 0 and len(d) > 0:
        last_row = d.iloc[-1]
        exit_px = float(last_row["Close"])
        _close_trade(exit_px, last_row.get("Date", last_row.get("index")), "End")

    if not trades or not equity_curve:
        return {}

    eq_df = pd.DataFrame(equity_curve)
    tdf_bt = pd.DataFrame(trades)

    # ── Professional Metrics (verbatim app.py:5980-6067) ────────────────
    final_equity = float(eq_df["equity"].iloc[-1])
    total_ret_pct = (final_equity - initial_capital) / initial_capital * 100.0

    n_days = len(eq_df)
    years = n_days / 252.0
    cagr = ((final_equity / initial_capital) ** (1.0 / years) - 1.0) * 100.0 if years > 0 else 0.0

    eq_series = eq_df["equity"]
    daily_ret = eq_series.pct_change().dropna()
    rf_daily = 0.06 / 252.0
    excess_ret = daily_ret - rf_daily
    sharpe = float(excess_ret.mean() / excess_ret.std() * np.sqrt(252)) if excess_ret.std() > 0 else 0.0

    downside = excess_ret[excess_ret < 0]
    sortino = float(excess_ret.mean() / downside.std() * np.sqrt(252)) if (len(downside) > 0 and downside.std() > 0) else 0.0

    roll_max = eq_series.cummax()
    drawdown = (eq_series - roll_max) / roll_max * 100.0
    max_dd = float(drawdown.min())
    calmar = abs(cagr / max_dd) if max_dd != 0 else 0.0

    in_dd = drawdown < 0
    dd_dur = 0
    cur_dur = 0
    for v in in_dd:
        cur_dur = cur_dur + 1 if v else 0
        dd_dur = max(dd_dur, cur_dur)

    total_trades = len(tdf_bt)
    wins = int(tdf_bt["win"].sum())
    losses = total_trades - wins
    win_rate = wins / total_trades * 100.0 if total_trades > 0 else 0.0

    avg_win = float(tdf_bt[tdf_bt["win"]]["pnl_pct"].mean()) if wins > 0 else 0.0
    avg_loss = abs(float(tdf_bt[~tdf_bt["win"]]["pnl_pct"].mean())) if losses > 0 else 0.0
    profit_factor = (
        float(tdf_bt[tdf_bt["win"]]["pnl"].sum() / abs(tdf_bt[~tdf_bt["win"]]["pnl"].sum()))
        if losses > 0 and tdf_bt[~tdf_bt["win"]]["pnl"].sum() != 0
        else float("inf")
    )

    expectancy = float(tdf_bt["pnl"].mean()) if total_trades > 0 else 0.0
    expectancy_pct = float(tdf_bt["pnl_pct"].mean()) if total_trades > 0 else 0.0
    avg_hold = float(tdf_bt["hold_days"].mean()) if total_trades > 0 else 0.0

    bh_start = float(df["Close"].iloc[0])
    bh_end = float(df["Close"].iloc[-1])
    bh_ret = (bh_end - bh_start) / bh_start * 100.0
    bh_cagr = ((bh_end / bh_start) ** (1.0 / max(years, 0.01)) - 1.0) * 100.0
    alpha = cagr - bh_cagr

    # Monthly returns for heatmap
    eq_df_copy = eq_df.copy()
    eq_df_copy["date"] = pd.to_datetime(eq_df_copy["date"], errors="coerce")
    eq_df_copy = eq_df_copy.dropna(subset=["date"])
    eq_df_copy.set_index("date", inplace=True)
    monthly = eq_df_copy["equity"].resample("ME").last().pct_change().dropna() * 100
    monthly_returns = [
        {"month": str(d.date())[:7], "return": round(float(v), 2)}
        for d, v in monthly.items()
    ]

    return {
        "final_equity": round(final_equity, 2),
        "total_ret_pct": round(total_ret_pct, 2),
        "cagr": round(cagr, 2),
        "sharpe": round(sharpe, 2),
        "sortino": round(sortino, 2),
        "calmar": round(calmar, 2),
        "max_dd": round(max_dd, 2),
        "dd_dur_days": dd_dur,
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else None,
        "expectancy": round(expectancy, 2),
        "expectancy_pct": round(expectancy_pct, 2),
        "avg_hold": round(avg_hold, 1),
        "years": round(years, 2),
        "bh_ret": round(bh_ret, 2),
        "bh_cagr": round(bh_cagr, 2),
        "alpha": round(alpha, 2),
        "initial_capital": initial_capital,
        "equity_curve": equity_curve,
        "trades": trades,
        "monthly_returns": monthly_returns,
    }


# ── Async API ───────────────────────────────────────────────────────────────


async def run_backtest(
    symbol: str,
    strategy: str,
    years: int = 5,
    initial_capital: float = 100_000.0,
    commission_pct: float = 0.1,
    sl_pct: float = 5.0,
    tp_pct: float = 0.0,
    position_size_pct: float = 100.0,
) -> dict:
    """Run a full backtest: download data → indicators → engine → metrics."""
    period = _PERIOD_MAP.get(years, "5y")
    candles = await market_data.get_history(symbol, "1d", period)

    def to_df() -> pd.DataFrame:
        if not candles:
            return pd.DataFrame()
        df = pd.DataFrame(candles)
        if "time" in df.columns and "Date" not in df.columns:
            df.rename(columns={"time": "Date"}, inplace=True)
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}, inplace=True)
        df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
        return df

    df = await anyio.to_thread.run_sync(to_df)
    if df.empty or len(df) < 60:
        return {}

    return await anyio.to_thread.run_sync(
        _run_backtest_sync,
        df,
        strategy,
        initial_capital,
        commission_pct,
        sl_pct,
        tp_pct,
        position_size_pct,
    )
