from __future__ import annotations

import numpy as np
import pandas as pd

from app.modules.sentiment import service

# ── RSS parsing (pure function, fixture XML — no network) ────────────────────


def test_extract_titles_prefers_cdata():
    xml = (
        "<rss><channel><title>Feed</title>"
        "<item><title><![CDATA[ Reliance surges on strong Q2 results ]]></title></item>"
        "<item><title><![CDATA[Short]]></title></item>"
        "</channel></rss>"
    )
    titles = service._extract_titles(xml)
    assert titles == ["Reliance surges on strong Q2 results"]


def test_extract_titles_falls_back_to_plain():
    xml = (
        "<rss><channel><title>Feed</title>"
        "<title>TCS wins large multi-year order from client</title>"
        "<title>ok</title>"
        "</channel></rss>"
    )
    titles = service._extract_titles(xml)
    assert titles == ["TCS wins large multi-year order from client"]


# ── News sentiment (keyword fallback path — FinBERT rarely installed) ─────────


def test_sentiment_bullish_headlines():
    out = service.get_sentiment_score(
        ["Reliance surges on record profits and strong growth",
         "Brokerages upgrade stock after Q2 beat"]
    )
    assert out["label"] == "BULLISH"
    assert out["score"] > 0.08
    assert all(d["label"] == "positive" for d in out["detail"])


def test_sentiment_bearish_headlines():
    out = service.get_sentiment_score(
        ["Stock plunges after SEBI probe and fraud concerns",
         "Brokerages downgrade after weak Q2 miss"]
    )
    assert out["label"] == "BEARISH"
    assert out["score"] < -0.08


def test_sentiment_neutral_for_empty_or_unknown_words():
    assert service.get_sentiment_score([]) == {
        "score": 0.0, "label": "NEUTRAL", "detail": [],
    }
    out = service.get_sentiment_score(["Company holds annual general meeting today"])
    assert out["label"] == "NEUTRAL"
    assert out["score"] == 0.0


def test_keyword_score_bounds():
    assert service._keyword_score("surge rally jump") == 1.0
    assert service._keyword_score("crash plunge loss") == -1.0
    assert service._keyword_score("no market words here") == 0.0


# ── Technical sentiment ────────────────────────────────────────────────────────


def tech_df(rsi=55.0, golden_cross=False, ret1d=0.0, vol_ratio=1.0) -> pd.DataFrame:
    """Minimal frame with the columns compute_technical_sentiment reads."""
    n = 60
    close = np.full(n, 100.0)
    close[-1] = close[-2] * (1 + ret1d)
    s20 = np.full(n, 98.0)
    s50 = np.full(n, 99.0)
    if golden_cross:
        s20[-2], s50[-2] = 98.0, 99.0
        s20[-1], s50[-1] = 100.5, 99.5
    else:
        s20[-1], s50[-1] = s20[-2], s50[-2]
    df = pd.DataFrame(
        {
            "Open": close, "High": close + 1, "Low": close - 1, "Close": close,
            "Volume": np.full(n, 1000.0 * vol_ratio),
            "RSI": np.full(n, rsi),
            "MACD": np.full(n, 1.0), "M_SIG": np.full(n, 0.5),
            "SMA_20": s20, "SMA_50": s50,
            "BB_H": close + 5, "BB_L": close - 5,
            "ATR": close * 0.015,
        },
        index=pd.date_range("2026-01-01", periods=n, freq="D"),
    )
    return df


def test_technical_sentiment_shape_and_bullish():
    out = service.compute_technical_sentiment(tech_df(rsi=60, golden_cross=True))
    assert {"score", "label", "signals", "raw_score"} <= set(out)
    assert out["label"] == "BULLISH"
    names = [s[0] for s in out["signals"]]
    assert "SMA" in names and "RSI" in names and "MACD" in names
    sma = next(s for s in out["signals"] if s[0] == "SMA")
    assert "Golden Cross" in sma[2]


def test_technical_sentiment_neutral_band():
    out = service.compute_technical_sentiment(tech_df(rsi=50, ret1d=0.0))
    assert out["label"] == "NEUTRAL"
    assert abs(out["score"]) <= 0.15


def test_technical_sentiment_survives_bare_frame():
    # Parity: any data hiccup degrades to neutral, never raises.
    bare = pd.DataFrame(
        {"Close": [100.0]},
        index=pd.date_range("2026-01-01", periods=1),
    )
    out = service.compute_technical_sentiment(bare)
    assert out["label"] == "NEUTRAL"


# ── Optional-dependency contract ───────────────────────────────────────────────


def test_finbert_keyword_path_always_scores():
    # With no model loaded the keyword path must still score every headline.
    service._FINBERT_PIPE = None
    out = service.get_sentiment_score(["Profits surge on strong demand"])
    assert len(out["detail"]) == 1
    assert out["label"] == "BULLISH"
