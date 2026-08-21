from __future__ import annotations

import anyio.to_thread
import pandas as pd

from app.modules.analytics.service import add_indicators, candles_to_df
from app.modules.market_data import service as market_data

# ── Signal engine (verbatim port of app.py:2170-2248) ────────────────────────
# Operates on the indicator-enriched frame from analytics.add_indicators.
# The two legacy output lists are kept intact: `signals` chips and `reasons`
# lines are index-independent in app.py, so they stay separate here too.


def compute_signal(df: pd.DataFrame) -> dict:
    signals: list[tuple[str, str]] = []
    reasons: list[str] = []
    score = 0
    n = len(df)

    if "RSI" in df.columns:
        rsi = float(df["RSI"].dropna().iloc[-1])
        if rsi < 30:
            signals.append(("RSI Oversold", "buy"))
            reasons.append(f"RSI {rsi:.1f} < 30 — oversold zone")
            score += 2
        elif rsi > 70:
            signals.append(("RSI Overbought", "sell"))
            reasons.append(f"RSI {rsi:.1f} > 70 — overbought zone")
            score -= 2
        elif 40 <= rsi <= 60:
            signals.append(("RSI Neutral", "neut"))
        elif rsi > 60:
            signals.append(("RSI Bullish", "buy"))
            score += 1
        else:
            signals.append(("RSI Bearish", "sell"))
            score -= 1

    if "MACD" in df.columns and "M_SIG" in df.columns:
        mn = float(df["MACD"].dropna().iloc[-1])
        sn = float(df["M_SIG"].dropna().iloc[-1])
        mp = float(df["MACD"].dropna().iloc[-2]) if len(df["MACD"].dropna()) > 1 else mn
        sp = float(df["M_SIG"].dropna().iloc[-2]) if len(df["M_SIG"].dropna()) > 1 else sn
        if mp < sp and mn > sn:
            signals.append(("MACD ↑ Cross", "buy"))
            reasons.append("MACD bullish crossover")
            score += 3
        elif mp > sp and mn < sn:
            signals.append(("MACD ↓ Cross", "sell"))
            reasons.append("MACD bearish crossover")
            score -= 3
        elif mn > sn:
            signals.append(("MACD Bullish", "buy"))
            score += 1
        else:
            signals.append(("MACD Bearish", "sell"))
            score -= 1

    if "SMA_20" in df.columns and "SMA_50" in df.columns:
        s20n = float(df["SMA_20"].dropna().iloc[-1])
        s50n = float(df["SMA_50"].dropna().iloc[-1])
        s20p = float(df["SMA_20"].dropna().iloc[-2]) if len(df["SMA_20"].dropna()) > 1 else s20n
        s50p = float(df["SMA_50"].dropna().iloc[-2]) if len(df["SMA_50"].dropna()) > 1 else s50n
        if s20p < s50p and s20n > s50n:
            signals.append(("Golden Cross 🌟", "buy"))
            reasons.append("SMA20 × SMA50 Golden Cross")
            score += 4
        elif s20p > s50p and s20n < s50n:
            signals.append(("Death Cross ☠️", "sell"))
            reasons.append("SMA20 × SMA50 Death Cross")
            score -= 4
        elif s20n > s50n:
            signals.append(("Above SMA50", "buy"))
            score += 1
        else:
            signals.append(("Below SMA50", "sell"))
            score -= 1

    if "SMA_20" in df.columns:
        sma20 = float(df["SMA_20"].dropna().iloc[-1])
        c = float(df["Close"].iloc[-1])
        if c > sma20 * 1.02:
            signals.append(("Above SMA20 +2%", "buy"))
            score += 1
        elif c < sma20 * 0.98:
            signals.append(("Below SMA20 -2%", "sell"))
            score -= 1
        else:
            signals.append(("Near SMA20", "neut"))

    if "BB_H" in df.columns:
        bh = float(df["BB_H"].dropna().iloc[-1])
        bl = float(df["BB_L"].dropna().iloc[-1])
        c = float(df["Close"].iloc[-1])
        if c > bh:
            signals.append(("BB Breakout ↑", "buy"))
            reasons.append("Price broke above BB upper")
            score += 2
        elif c < bl:
            signals.append(("BB Breakdown ↓", "sell"))
            reasons.append("Price broke below BB lower")
            score -= 2
        else:
            signals.append(("Inside BB", "neut"))

    if "Volume" in df.columns and n > 20:
        avg_v = float(df["Volume"].tail(20).mean())
        lv = float(df["Volume"].iloc[-1])
        lc = float(df["Close"].iloc[-1]) - float(df["Close"].iloc[-2]) if n > 1 else 0
        if lv > avg_v * 1.5 and lc > 0:
            signals.append(("High Vol + Up", "buy"))
            reasons.append(f"Volume {lv / avg_v:.1f}× avg with price up")
            score += 2
        elif lv > avg_v * 1.5 and lc < 0:
            signals.append(("High Vol + Down", "sell"))
            reasons.append(f"Volume {lv / avg_v:.1f}× avg with price down")
            score -= 2
        else:
            signals.append(("Normal Volume", "neut"))

    if score >= 5:
        verdict = "BUY"
    elif score <= -5:
        verdict = "SELL"
    elif score >= 2:
        verdict = "WEAK BUY"
    elif score <= -2:
        verdict = "WEAK SELL"
    else:
        verdict = "HOLD"

    # ── Confidence: blended formula (floor 50%, range 50–100%) ───
    directional = [(lb, k) for lb, k in signals if k in ("buy", "sell")]
    if directional:
        dominant = "buy" if score >= 0 else "sell"
        agree = sum(1 for _, k in directional if k == dominant)
        agreement_ratio = agree / len(directional)
    else:
        agreement_ratio = 0.5

    score_norm = min(abs(score) / 7.0, 1.0)
    raw_conf = 0.60 * agreement_ratio + 0.40 * score_norm
    confidence = 0.50 + 0.50 * raw_conf

    return {
        "verdict": verdict,
        "score": score,
        "confidence": confidence,
        "signals": [{"rule": label, "kind": kind} for label, kind in signals],
        "reasons": reasons,
    }


# ── Buy/Sell markers (verbatim port of app.py:2253-2267) ─────────────────────


def generate_markers(df: pd.DataFrame) -> list[dict]:
    bd, bp, sd, sp = [], [], [], []
    if "MACD" not in df.columns or "M_SIG" not in df.columns:
        return []
    macd = df["MACD"].ffill()
    sig = df["M_SIG"].ffill()
    rsi = df["RSI"].fillna(50) if "RSI" in df.columns else pd.Series(50, index=df.index)
    for i in range(1, len(df)):
        pd_ = float(macd.iloc[i - 1]) - float(sig.iloc[i - 1])
        cd = float(macd.iloc[i]) - float(sig.iloc[i])
        rv = float(rsi.iloc[i])
        cl = float(df["Close"].iloc[i])
        if pd_ < 0 and cd > 0 and rv < 65:
            bd.append(df.index[i])
            bp.append(cl * 0.993)
        elif pd_ > 0 and cd < 0 and rv > 35:
            sd.append(df.index[i])
            sp.append(cl * 1.007)

    out = [
        {"time": ts.isoformat(), "position": "belowBar", "kind": "buy", "price": p}
        for ts, p in zip(bd, bp)
    ]
    out += [
        {"time": ts.isoformat(), "position": "aboveBar", "kind": "sell", "price": p}
        for ts, p in zip(sd, sp)
    ]
    return sorted(out, key=lambda m: m["time"])


# ── Async API ─────────────────────────────────────────────────────────────────


async def get_signal(symbol: str, interval, period) -> dict:
    candles = await market_data.get_history(symbol, interval, period)

    def compute() -> dict:
        df = add_indicators(candles_to_df(candles))
        result = compute_signal(df)
        result["markers"] = generate_markers(df)
        return result

    return await anyio.to_thread.run_sync(compute)
