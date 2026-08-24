from __future__ import annotations

from typing import Any

import anyio.to_thread
import numpy as np
import pandas as pd

from app.modules.analytics.service import add_indicators, candles_to_df
from app.modules.market_data import service as market_data
from app.modules.market_data.service import Interval, Period

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


# ── 3-Layer Signal Fusion (verbatim port of app.py:3391-3455) ──────────────
# Weights: Technical 45% + ML 40% + News 15% — same numbers as app.py:3411-3413.
# Graceful degradation: if ML or news is unavailable, the remaining layers
# are re-weighted proportionally so the result is still meaningful.


_TECH_W = 0.45
_ML_W = 0.40
_NEWS_W = 0.15


def _normalise_label(label: str) -> str:
    """Map any label to BULLISH / BEARISH / NEUTRAL."""
    upper = label.strip().upper()
    if upper in ("BULLISH", "POSITIVE", "UP"):
        return "BULLISH"
    if upper in ("BEARISH", "NEGATIVE", "DOWN"):
        return "BEARISH"
    return "NEUTRAL"


def compute_fusion(
    tech_result: dict,
    ml_result: dict[str, Any] | None,
    news_result: dict[str, Any] | None,
) -> dict:
    """Blend technical + ML + news into a single fused verdict.

    Parameters
    ----------
    tech_result:
        Output of ``compute_signal`` (verdict, score, confidence, signals, reasons).
    ml_result:
        Full ``run_ml`` output dict, or ``None`` if unavailable.
    news_result:
        Output of ``get_sentiment_score`` (score, label, detail), or ``None``.
    """
    # ── Technical layer ──────────────────────────────────────────────────
    # compute_signal returns an integer score (typically −18..+18).
    # Normalise to −1..+1 by dividing by a reasonable max.
    tech_score_raw = float(tech_result.get("score", 0))
    ts_score = float(np.clip(tech_score_raw / 12.0, -1.0, 1.0))
    ts_label = "BULLISH" if tech_score_raw >= 5 else "BEARISH" if tech_score_raw <= -5 else "NEUTRAL"
    ts_signals = tech_result.get("signals", [])
    ts_reasons = tech_result.get("reasons", [])

    # ── ML layer ─────────────────────────────────────────────────────────
    ml_available = False
    ml_score = 0.0
    ml_label = "NEUTRAL"
    ml_up_prob = 50.0
    ml_confidence = 50.0
    ml_horizon: dict[str, Any] = {}
    ml_model_accs: dict[str, float] = {}
    ml_conf_tier: dict[str, str] = {}
    ml_walk_fwd = 0.0
    ml_active_models = ""

    if ml_result is not None:
        ml_available = True
        ml_up_prob = float(ml_result.get("up_prob", 50.0))
        ml_score = (ml_up_prob - 50.0) / 50.0  # −1..+1
        ml_label = _normalise_label(ml_result.get("direction", "neutral"))
        ml_confidence = float(ml_result.get("confidence", 50.0))
        ml_horizon = ml_result.get("horizon", {})
        ml_model_accs = ml_result.get("model_accs", {})
        ml_conf_tier = ml_result.get("conf_tier", {})
        ml_walk_fwd = float(ml_result.get("walk_fwd_acc", 0.0))
        ml_active_models = ml_result.get("active_models", "")

    # ── News layer ───────────────────────────────────────────────────────
    news_available = False
    ns_score = 0.0
    ns_label = "NEUTRAL"
    ns_detail: list[dict] = []

    if news_result is not None:
        ns_score = float(news_result.get("score", 0.0))
        ns_label = _normalise_label(news_result.get("label", "neutral"))
        ns_detail = news_result.get("detail", [])
        if ns_score != 0.0:
            news_available = True

    # ── Re-weight if layers missing ──────────────────────────────────────
    available_weights = []
    available_scores = []
    if True:  # technical always available
        available_weights.append(_TECH_W)
        available_scores.append(ts_score)
    if ml_available:
        available_weights.append(_ML_W)
        available_scores.append(ml_score)
    if news_available:
        available_weights.append(_NEWS_W)
        available_scores.append(ns_score)

    total_w = sum(available_weights)
    fused_score = sum(w / total_w * s for w, s in zip(available_weights, available_scores))
    fused_score = float(np.clip(fused_score, -1.0, 1.0))

    # ── Final verdict (thresholds from app.py:3418-3452) ─────────────────
    if fused_score >= 0.35:
        final_label = "STRONG BUY"
        final_desc = "All 3 layers aligned bullish. High conviction upside expected."
    elif fused_score >= 0.12:
        final_label = "BUY"
        final_desc = "Majority signals favour upside. Moderate bullish bias."
    elif fused_score <= -0.35:
        final_label = "STRONG SELL"
        final_desc = "All 3 layers aligned bearish. High conviction downside expected."
    elif fused_score <= -0.12:
        final_label = "SELL"
        final_desc = "Majority signals favour downside. Moderate bearish bias."
    else:
        final_label = "NEUTRAL"
        final_desc = "Mixed signals across layers. Avoid fresh positions, hold existing ones."

    # ── Confidence tier (composite of available layers) ───────────────────
    agreement_count = 0
    agreement_total = 0
    layers_bullish = [ts_label, ml_label, ns_label]
    direction_labels = [l for l in layers_bullish if l != "NEUTRAL"]

    if direction_labels:
        dominant_dir = max(set(direction_labels), key=direction_labels.count)
        agreement_count = sum(1 for l in direction_labels if l == dominant_dir)
        agreement_total = len(direction_labels)

    if agreement_total == 0:
        conf_tier = "LOW"
        conf_tone = "Weak conviction — mixed or missing layers."
    elif agreement_count == agreement_total and agreement_total >= 2:
        conf_tier = "HIGH"
        conf_tone = "All available layers agree."
    else:
        conf_tier = "MEDIUM"
        conf_tone = "Some layers disagree."

    # ── What's missing ───────────────────────────────────────────────────
    missing: list[str] = []
    if not ml_available:
        missing.append("ML prediction not available — training data insufficient.")
    if not news_available:
        missing.append("News sentiment unavailable — no headlines fetched.")

    return {
        "fused_score": round(fused_score, 4),
        "final_label": final_label,
        "final_desc": final_desc,
        "confidence_tier": conf_tier,
        "confidence_tone": conf_tone,
        "missing": missing,
        "layers": {
            "technical": {
                "score": round(ts_score, 4),
                "label": ts_label,
                "weight": _TECH_W,
                    "signals": [{"rule": s.get("rule", ""), "kind": s.get("kind", "neut")} for s in ts_signals[:8]],
                "reasons": ts_reasons,
            },
            "ml": {
                "score": round(ml_score, 4),
                "label": ml_label,
                "weight": _ML_W,
                "available": ml_available,
                "up_prob": ml_up_prob,
                "confidence": ml_confidence,
                "horizon": ml_horizon,
                "model_accs": ml_model_accs,
                "conf_tier": ml_conf_tier,
                "walk_fwd_acc": ml_walk_fwd,
                "active_models": ml_active_models,
            },
            "news": {
                "score": round(ns_score, 4),
                "label": ns_label,
                "weight": _NEWS_W,
                "available": news_available,
                "detail": ns_detail[:6],
            },
        },
    }


# ── Async fusion API ────────────────────────────────────────────────────────


async def get_fusion(
    symbol: str,
    interval: Interval = "1d",
    period: Period = "2y",
) -> dict[str, Any]:
    """Compute fused signal: technical + ML + news."""
    # 1. Technical signal (fast, always works)
    tech = await get_signal(symbol, interval, period)

    # 2. ML prediction (try cached first, else run fresh)
    ml_result: dict[str, Any] | None = None
    try:
        from app.modules.ml.service import predict
        ml_result = await predict(symbol, use_lstm=False)
    except Exception:  # noqa: BLE001, S110 — ML degradation is expected
        pass

    # 3. News sentiment
    news_result: dict[str, Any] | None = None
    try:
        from app.modules.sentiment.service import get_headlines, get_sentiment_score
        headlines = await get_headlines(symbol, max_items=8)
        if headlines:
            news_result = await anyio.to_thread.run_sync(
                get_sentiment_score, headlines
            )
    except Exception:  # noqa: BLE001, S110 — news degradation is expected
        pass

    def compute() -> dict:
        return compute_fusion(tech, ml_result, news_result)

    return await anyio.to_thread.run_sync(compute)
