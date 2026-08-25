"""Sentiment module — news headlines + news/technical sentiment scoring.

Ports (verbatim math and thresholds):
- fetch_news_headlines      (app.py:77)   Yahoo RSS → Google News RSS → yfinance
- get_sentiment_score       (app.py:2306) FinBERT 70% + keyword 30% blend
- compute_technical_sentiment (app.py:2402) 10 rule signals from indicators
"""

from __future__ import annotations

import logging
import re
from typing import Any

import anyio.to_thread
import numpy as np
import pandas as pd
import requests

from app.core.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

NEWS_TTL = 600  # headlines change slowly; be polite to the RSS hosts

_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ── Optional FinBERT (lazy, capability-flagged — parity app.py:46-49) ────────
try:  # pragma: no cover - depends on optional transformers install
    from transformers import pipeline as hf_pipeline

    FINBERT_OK = True
except ImportError:
    hf_pipeline = None
    FINBERT_OK = False

_FINBERT_PIPE: Any = None


# ── News headlines (verbatim port of app.py:77-126) ─────────────────────────

def _extract_titles(xml: str) -> list[str]:
    """CDATA titles first, then plain <title> rows (row 0 is the feed name)."""
    titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", xml)
    if not titles:
        titles = re.findall(r"<title>(.*?)</title>", xml)
        # Skip the feed-level title (row 0) — same as Google News fallback
        if titles:
            titles = titles[1:]
    return [
        t.strip()
        for t in titles
        if len(t.strip()) > 20 and "Yahoo! Finance" not in t
    ]


def _fetch_headlines_sync(symbol: str, max_items: int) -> list[str]:
    clean = symbol.replace(".NS", "").replace(".BO", "").replace("^", "")
    headlines: list[str] = []

    # Attempt 1: Yahoo Finance RSS
    try:
        rss_url = (
            f"https://feeds.finance.yahoo.com/rss/2.0/headline"
            f"?s={symbol}&region=IN&lang=en-IN"
        )
        resp = requests.get(rss_url, timeout=7, headers=_UA)
        if resp.status_code == 200:
            headlines = _extract_titles(resp.text)[:max_items]
    except Exception:  # noqa: BLE001, S110 - RSS attempt is best-effort (parity app.py)
        pass

    # Attempt 2: Google News RSS fallback
    if not headlines:
        try:
            query = f"{clean}+stock+NSE+India"
            rss_url2 = (
                f"https://news.google.com/rss/search?q={query}"
                f"&hl=en-IN&gl=IN&ceid=IN:en"
            )
            resp2 = requests.get(rss_url2, timeout=7, headers=_UA)
            if resp2.status_code == 200:
                titles2 = re.findall(r"<title>(.*?)</title>", resp2.text)[1:]
                headlines = [
                    t.strip() for t in titles2 if len(t.strip()) > 20
                ][:max_items]
        except Exception:  # noqa: BLE001, S110 - RSS attempt is best-effort
            pass

    # Attempt 3: yfinance .news
    if not headlines:
        try:
            import yfinance as yf

            tk = yf.Ticker(symbol)
            for item in (tk.news or [])[:max_items]:
                title = item.get("title", "")
                if title and len(title) > 10:
                    headlines.append(title)
        except Exception:  # noqa: BLE001, S110 - yfinance news is best-effort
            pass

    return headlines


async def get_headlines(symbol: str, max_items: int = 8) -> list[str]:
    key = f"sentiment:news:{symbol}:{max_items}"
    cached = await cache_get(key)
    if cached is not None:
        return cached
    headlines = await anyio.to_thread.run_sync(
        _fetch_headlines_sync, symbol, max_items
    )
    await cache_set(key, headlines, NEWS_TTL)
    return headlines


# ── News sentiment (verbatim port of app.py:2306-2400) ──────────────────────

BULL_WORDS = [
    "surge","surges","surged","rally","rallies","rallied","jump","jumps","jumped",
    "gain","gains","gained","rise","rises","rose","soar","soars","soared",
    "breakout","outperform","upgrade","upgraded","buy","strong buy","accumulate",
    "beat","beats","exceeded","profit","profits","record","high","52-week high",
    "bullish","positive","growth","expansion","order","orders","win","wins","won",
    "contract","partnership","acquisition","dividend","buyback","demerger",
    "capex","investment","launch","launches","approved","nod","clearance",
    "robust","healthy","strong","stellar","better than expected","above estimate",
    "q-o-q growth","yoy growth","revenue up","pat up","ebitda up","margin expand",
    "upside","overweight","add","target price raised","target raised",
]
BEAR_WORDS = [
    "fall","falls","fell","drop","drops","dropped","decline","declines","declined",
    "crash","crashes","slump","slumps","slumped","plunge","plunges","plunged",
    "loss","losses","sell","downgrade","downgraded","weak","miss","missed",
    "below estimate","disappoint","disappoints","disappointed","warning","warn",
    "bearish","negative","concern","concerns","risk","risks","debt","default",
    "fraud","scam","probe","investigation","seizure","raid","ban","penalty",
    "fine","charged","income tax","ed notice","sebi action","npa","bad loan",
    "write-off","impairment","revenue down","pat down","ebitda down",
    "margin shrink","margin pressure","underweight","sell rating","target cut",
    "52-week low","lower circuit","halt","suspension","delist",
]


def _keyword_score(text: str) -> float:
    t = text.lower()
    bull = sum(1 for w in BULL_WORDS if w in t)
    bear = sum(1 for w in BEAR_WORDS if w in t)
    total = bull + bear
    if total == 0:
        return 0.0
    return float((bull - bear) / total)


def _load_finbert():
    global _FINBERT_PIPE
    if _FINBERT_PIPE is None and FINBERT_OK:
        try:
            _FINBERT_PIPE = hf_pipeline(
                "sentiment-analysis", model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert", truncation=True, max_length=512,
            )
        except Exception:  # noqa: BLE001 - model load is best-effort
            _FINBERT_PIPE = None
    return _FINBERT_PIPE


def get_sentiment_score(headlines: list) -> dict:
    """
    Layer 1 — FinBERT (if installed), Layer 2 — keyword fallback.
    Blend: FinBERT 70% + keyword 30% when both available.
    Returns score in [-1, +1], label BULLISH/BEARISH/NEUTRAL, per-headline detail.
    """
    results: list[dict] = []
    scored: list[float] = []

    pipe = _load_finbert()
    lmap = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}

    for h in (headlines or [])[:10]:
        h_clean = h.strip()
        if not h_clean:
            continue
        finbert_val = None
        finbert_lbl = None
        if pipe:
            try:
                out = pipe(h_clean[:512])[0]
                finbert_val = lmap.get(out["label"].lower(), 0.0) * out["score"]
                finbert_lbl = out["label"].lower()
            except Exception:  # noqa: BLE001, S110 - per-headline scoring best-effort
                pass

        kw_val = _keyword_score(h_clean)

        if finbert_val is not None:
            val = 0.70 * finbert_val + 0.30 * kw_val
            lbl = finbert_lbl
        else:
            val = kw_val
            lbl = "positive" if kw_val > 0.1 else "negative" if kw_val < -0.1 else "neutral"

        scored.append(val)
        results.append({
            "headline": h_clean[:90],
            "label": lbl,
            "conf": round(abs(val), 3),
            "score": round(val, 3),
        })

    if not scored:
        return {"score": 0.0, "label": "NEUTRAL", "detail": []}

    avg = float(np.mean(scored))
    if avg > 0.08:
        label = "BULLISH"
    elif avg < -0.08:
        label = "BEARISH"
    else:
        label = "NEUTRAL"
    return {"score": round(avg, 4), "label": label, "detail": results}


# ── Technical sentiment (verbatim port of app.py:2402-2577, minus emoji) ─────

def compute_technical_sentiment(df: pd.DataFrame) -> dict:
    """Rule-based technical sentiment — 10 independent indicator signals."""
    signals: list[tuple[str, str, str, float]] = []
    score = 0.0

    try:
        close = df["Close"].dropna()
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) > 1 else last
        ret1d = (last - prev) / prev if prev else 0

        # 1. RSI
        if "RSI" in df.columns:
            rsi = float(df["RSI"].dropna().iloc[-1])
            if rsi > 70:
                signals.append(("RSI", "BEARISH", f"RSI {rsi:.1f} — overbought", -0.6))
                score -= 0.6
            elif rsi < 30:
                signals.append(("RSI", "BULLISH", f"RSI {rsi:.1f} — oversold bounce", 0.7))
                score += 0.7
            elif rsi > 55:
                signals.append(("RSI", "BULLISH", f"RSI {rsi:.1f} — bullish zone", 0.3))
                score += 0.3
            elif rsi < 45:
                signals.append(("RSI", "BEARISH", f"RSI {rsi:.1f} — bearish zone", -0.3))
                score -= 0.3
            else:
                signals.append(("RSI", "NEUTRAL", f"RSI {rsi:.1f} — neutral", 0.0))

        # 2. MACD crossover
        if "MACD" in df.columns and "M_SIG" in df.columns:
            macd_now = float(df["MACD"].dropna().iloc[-1])
            sig_now = float(df["M_SIG"].dropna().iloc[-1])
            macd_prev = float(df["MACD"].dropna().iloc[-2]) if len(df["MACD"].dropna()) > 1 else macd_now
            sig_prev = float(df["M_SIG"].dropna().iloc[-2]) if len(df["M_SIG"].dropna()) > 1 else sig_now
            if macd_prev < sig_prev and macd_now > sig_now:
                signals.append(("MACD", "BULLISH", "MACD bullish crossover", 0.9))
                score += 0.9
            elif macd_prev > sig_prev and macd_now < sig_now:
                signals.append(("MACD", "BEARISH", "MACD bearish crossover", -0.9))
                score -= 0.9
            elif macd_now > sig_now:
                signals.append(("MACD", "BULLISH", "MACD above signal", 0.4))
                score += 0.4
            else:
                signals.append(("MACD", "BEARISH", "MACD below signal", -0.4))
                score -= 0.4

        # 3. SMA 20/50 trend
        if "SMA_20" in df.columns and "SMA_50" in df.columns:
            s20 = float(df["SMA_20"].dropna().iloc[-1])
            s50 = float(df["SMA_50"].dropna().iloc[-1])
            s20p = float(df["SMA_20"].dropna().iloc[-2]) if len(df["SMA_20"].dropna()) > 1 else s20
            s50p = float(df["SMA_50"].dropna().iloc[-2]) if len(df["SMA_50"].dropna()) > 1 else s50
            if s20p < s50p and s20 > s50:
                signals.append(("SMA", "BULLISH", "Golden Cross — SMA20 > SMA50", 1.0))
                score += 1.0
            elif s20p > s50p and s20 < s50:
                signals.append(("SMA", "BEARISH", "Death Cross — SMA20 < SMA50", -1.0))
                score -= 1.0
            elif s20 > s50:
                signals.append(("SMA", "BULLISH", "Price above SMA50 trend", 0.4))
                score += 0.4
            else:
                signals.append(("SMA", "BEARISH", "Price below SMA50 — downtrend", -0.4))
                score -= 0.4

        # 4. Price vs SMA20
        if "SMA_20" in df.columns:
            s20 = float(df["SMA_20"].dropna().iloc[-1])
            dist = (last - s20) / s20 * 100
            if dist > 3:
                signals.append(("SMA20", "BULLISH", f"Price {dist:+.1f}% above SMA20", 0.4))
                score += 0.4
            elif dist < -3:
                signals.append(("SMA20", "BEARISH", f"Price {dist:+.1f}% below SMA20", -0.4))
                score -= 0.4
            else:
                signals.append(("SMA20", "NEUTRAL", f"Price near SMA20 ({dist:+.1f}%)", 0.0))

        # 5. Bollinger Band
        if "BB_H" in df.columns and "BB_L" in df.columns:
            bh = float(df["BB_H"].dropna().iloc[-1])
            bl = float(df["BB_L"].dropna().iloc[-1])
            if last > bh:
                signals.append(("BB", "BULLISH", "BB breakout above upper band", 0.6))
                score += 0.6
            elif last < bl:
                signals.append(("BB", "BEARISH", "BB breakdown below lower band", -0.6))
                score -= 0.6
            elif last > (bh + bl) / 2:
                signals.append(("BB", "BULLISH", "Price in upper BB half", 0.2))
                score += 0.2
            else:
                signals.append(("BB", "BEARISH", "Price in lower BB half", -0.2))
                score -= 0.2

        # 6. Volume spike
        if "Volume" in df.columns and len(df) > 20:
            vol_avg = float(df["Volume"].tail(20).mean())
            vol_now = float(df["Volume"].iloc[-1])
            vratio = vol_now / (vol_avg + 1e-9)
            if vratio > 1.5 and ret1d > 0:
                signals.append(("Volume", "BULLISH", f"Vol {vratio:.1f}x avg — buyers in control", 0.7))
                score += 0.7
            elif vratio > 1.5 and ret1d < 0:
                signals.append(("Volume", "BEARISH", f"Vol {vratio:.1f}x avg — sellers in control", -0.7))
                score -= 0.7
            else:
                signals.append(("Volume", "NEUTRAL", f"Normal volume ({vratio:.1f}x)", 0.0))

        # 7. 1-day momentum
        if ret1d > 0.02:
            signals.append(("Momentum", "BULLISH", f"Strong +{ret1d*100:.1f}% today", 0.5))
            score += 0.5
        elif ret1d < -0.02:
            signals.append(("Momentum", "BEARISH", f"Weak {ret1d*100:.1f}% today", -0.5))
            score -= 0.5
        else:
            signals.append(("Momentum", "NEUTRAL", f"Flat {ret1d*100:+.2f}% today", 0.0))

        # 8. ATR volatility regime
        if "ATR" in df.columns:
            atr = float(df["ATR"].dropna().iloc[-1])
            atr_pct = atr / last * 100
            if atr_pct > 3:
                signals.append(("ATR", "BEARISH", f"High volatility ATR {atr_pct:.1f}% — risky", -0.2))
                score -= 0.2
            elif atr_pct < 1:
                signals.append(("ATR", "NEUTRAL", f"Low ATR {atr_pct:.1f}% — squeeze", 0.0))
            else:
                signals.append(("ATR", "NEUTRAL", f"Normal ATR {atr_pct:.1f}%", 0.0))

        # 9. 5-day momentum
        if len(close) >= 6:
            r5 = (last / float(close.iloc[-6]) - 1) * 100
            if r5 > 5:
                signals.append(("5D Trend", "BULLISH", f"5-day return +{r5:.1f}%", 0.5))
                score += 0.5
            elif r5 < -5:
                signals.append(("5D Trend", "BEARISH", f"5-day return {r5:.1f}%", -0.5))
                score -= 0.5
            else:
                signals.append(("5D Trend", "NEUTRAL", f"5-day return {r5:+.1f}%", 0.0))

        # 10. 21-day momentum
        if len(close) >= 22:
            r21 = (last / float(close.iloc[-22]) - 1) * 100
            if r21 > 10:
                signals.append(("21D Trend", "BULLISH", f"21-day return +{r21:.1f}%", 0.5))
                score += 0.5
            elif r21 < -10:
                signals.append(("21D Trend", "BEARISH", f"21-day return {r21:.1f}%", -0.5))
                score -= 0.5
            else:
                signals.append(("21D Trend", "NEUTRAL", f"21-day return {r21:+.1f}%", 0.0))

    except Exception:  # noqa: BLE001, S110 — parity: any data hiccup degrades to neutral
        pass

    max_possible = 7.0
    norm = float(np.clip(score / max_possible, -1.0, 1.0))

    if norm > 0.15:
        label = "BULLISH"
    elif norm < -0.15:
        label = "BEARISH"
    else:
        label = "NEUTRAL"

    return {"score": round(norm, 4), "label": label, "signals": signals, "raw_score": round(score, 2)}
