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
        "score": 0.0, "label": "NEUTRAL", "detail": [], "isStoredData": False,
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


def test_live_scores_are_flagged_as_not_stored():
    # The live path is never the archive — the flag has to say so, otherwise
    # the frontend cannot tell the two apart.
    out = service.get_sentiment_score(["Profits surge on strong demand"])
    assert out["isStoredData"] is False


# ── Insight: stored first, live fallback ─────────────────────────────────────


STORED_BUNDLE = {
    "symbol": "TCS.NS",
    "score": 0.1124,
    "label": "BULLISH",
    "article_count": 891,
    "counts": {"positive": 120, "neutral": 640, "negative": 131},
    "avg_confidence": 0.71,
    "window": {"start": "2024-01-10", "end": "2026-10-05"},
    "periods": {
        "1m": {
            "period": "1m",
            "title": "1M",
            "days": 30,
            "available": True,
            "score": 0.24,
            "label": "BULLISH",
            "article_count": 41,
            "pos_count": 12,
            "neu_count": 20,
            "neg_count": 9,
            "avg_confidence": 0.7,
            "sentiment_change": 0.1,
            "window_start": None,
            "window_end": None,
            "price_start": 3000.0,
            "price_end": 3100.0,
            "price_change_pct": 3.3,
        }
    },
    "articles": [
        {
            "id": 1,
            "title": "TCS Q2 results: Net profit up 1.4%",
            "source": "Business Standard",
            "published_at": "2026-10-05T00:00:00+00:00",
            "url": "https://example.com/1",
            "score": 0.9681,
            "label": "BULLISH",
        }
    ],
    "top_positive": [{"title": "TCS Q2 results: Net profit up 1.4%", "score": 0.9681}],
    "top_negative": [{"title": "TCS headcount drops to less than 600k", "score": -0.9821}],
    "model_version": "prosusai-finbert",
    "updated_at": "2026-10-07T16:10:00+00:00",
}


def _patch_stored(monkeypatch, bundle):
    from app.modules.news.sentiment import service as stored_service

    async def fake_bundle(symbol, article_limit=12):
        return bundle

    monkeypatch.setattr(stored_service, "get_symbol_bundle", fake_bundle)


def _patch_technical(monkeypatch):
    async def fake_technical(symbol, interval="1d", period="2y"):
        return {
            "score": 0.4,
            "label": "BULLISH",
            "raw_score": 2.8,
            "signals": [("SMA", "BULLISH", "Golden Cross — SMA20 > SMA50", 1.0)],
        }

    monkeypatch.setattr(service, "get_technical_sentiment", fake_technical)


async def test_insight_serves_stored_data_when_the_stock_is_covered(monkeypatch):
    _patch_stored(monkeypatch, STORED_BUNDLE)
    _patch_technical(monkeypatch)

    async def no_headlines(*args, **kwargs):
        raise AssertionError("the live scrape must not run when we have coverage")

    monkeypatch.setattr(service, "get_headlines", no_headlines)

    out = await service.get_insight("tcs.ns")

    assert out["isStoredData"] is True
    assert out["source"] == "stored"
    assert out["news"]["score"] == 0.1124
    assert out["news"]["label"] == "BULLISH"
    assert out["news"]["article_count"] == 891
    assert out["news"]["counts"]["negative"] == 131
    assert out["news"]["detail"][0]["label"] == "positive"
    assert out["periods"]["1m"]["score"] == 0.24
    assert out["top_articles"][0]["title"].startswith("TCS Q2 results")
    assert out["top_negative"][0]["score"] == -0.9821
    assert out["model_version"] == "prosusai-finbert"
    assert out["technical"]["signals"][0]["name"] == "SMA"


async def test_insight_falls_back_to_live_when_nothing_is_stored(monkeypatch):
    _patch_stored(monkeypatch, None)
    _patch_technical(monkeypatch)

    async def fake_headlines(symbol, max_items=8):
        return ["TCS wins a large multi-year order from a client"]

    monkeypatch.setattr(service, "get_headlines", fake_headlines)

    out = await service.get_insight("TCS.NS")

    assert out["isStoredData"] is False
    assert out["source"] == "live"
    assert out["news"]["detail"][0]["headline"].startswith("TCS wins")
    assert out["periods"] == {}
    assert out["top_articles"] == []
    assert out["model_version"] is None


async def test_insight_survives_a_broken_store(monkeypatch):
    from app.modules.news.sentiment import service as stored_service

    async def boom(symbol, article_limit=12):
        raise RuntimeError("news database is down")

    monkeypatch.setattr(stored_service, "get_symbol_bundle", boom)

    async def fake_headlines(symbol, max_items=8):
        return ["Reliance surges on record profits"]

    monkeypatch.setattr(service, "get_headlines", fake_headlines)
    _patch_technical(monkeypatch)

    out = await service.get_insight("RELIANCE.NS")

    # A broken store must not take the page down: we fall back to the live path.
    assert out["isStoredData"] is False
    assert out["news"]["label"] == "BULLISH"


async def test_deprecated_endpoints_answer_with_a_notice():
    from fastapi import Response

    from app.modules.sentiment import router as sentiment_router

    response = Response()
    news = await sentiment_router.news_deprecated(response=response, symbol="TCS.NS")
    score = await sentiment_router.score_deprecated(response=response, symbol="TCS.NS")

    for payload in (news, score):
        assert payload.deprecated is True
        assert payload.replacement == "/sentiment/insight"
        assert "deprecated" in payload.message.lower()
        assert payload.symbol == "TCS.NS"
