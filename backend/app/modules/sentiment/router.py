"""Sentiment endpoints.

`GET /sentiment/insight` is the one the frontend uses. It serves **stored**
sentiment when the stock has any (our archive of scored headlines, with the
1M/3M/1Y/3Y breakdown and the strongest stories) and falls back to the live
scrape when it does not. The `isStoredData` flag says which of the two happened.

`GET /sentiment/score` and `GET /sentiment/news` are **deprecated**. Their
controllers are kept below, commented out, so the old behaviour stays readable
in the history of this file — the routes now answer with a short deprecation
notice pointing at the replacement.
"""

from fastapi import APIRouter, Depends, Query, Response

from app.core.config import settings
from app.core.deps import get_current_user
from app.modules.market_data.service import Interval, Period
from app.modules.sentiment import service
from app.modules.sentiment.schemas import (
    DeprecatedResponse,
    SentimentInsightResponse,
)

router = APIRouter(
    prefix="/sentiment",
    tags=["sentiment"],
    dependencies=[Depends(get_current_user)],
)

# Shown by the deprecated routes. Kept in one place so both say the same thing.
DEPRECATION_MESSAGE = (
    "This endpoint is deprecated and no longer computes anything. "
    "Use GET /sentiment/insight instead — it serves stored sentiment when we "
    "have it and falls back to a live scrape when we do not."
)
REPLACEMENT = "/sentiment/insight"
REPLACEMENT_PATH = f"{settings.api_v1_prefix}{REPLACEMENT}"


@router.get(
    "/insight",
    response_model=SentimentInsightResponse,
    summary="News sentiment for a stock — stored archive first, live scrape as fallback",
    description=(
        "The endpoint the frontend uses for the news-and-mood card.\n\n"
        "**Stored first.** For a stock we have scraped, the answer comes from "
        "our archive of scored headlines: the overall score, the 1M / 3M / 1Y / "
        "3Y breakdown, the strongest positive and negative stories and the "
        "most recent articles. It is a database read — no scraping, no model.\n\n"
        "**Live fallback.** For a stock we have never scraped there is nothing "
        "stored, so the headlines are scraped and scored on the spot.\n\n"
        "`isStoredData` tells the two apart: `true` for the archive, `false` for "
        "a live scrape. The frontend uses it to show which kind of number the "
        "user is looking at."
    ),
)
async def insight(
    symbol: str = Query(..., min_length=1, max_length=32),
    interval: Interval = Query("1d"),
    period: Period = Query("2y"),
) -> SentimentInsightResponse:
    data = await service.get_insight(symbol, interval, period)
    return SentimentInsightResponse(**data)


# ── Deprecated: /sentiment/news ──────────────────────────────────────────────
# Replaced by `/sentiment/insight`, which returns the live headlines inside the
# full payload instead of on their own. The controller is kept here, commented
# out, so the old behaviour stays readable.
#
# @router.get("/news", response_model=NewsResponse)
# async def news(
#     symbol: str = Query(..., min_length=1, max_length=32),
#     max_items: int = Query(8, ge=1, le=20),
# ) -> NewsResponse:
#     clean = symbol.strip().upper()
#     headlines = await service.get_headlines(clean, max_items)
#     return NewsResponse(symbol=clean, count=len(headlines), headlines=headlines)


@router.get(
    "/news",
    response_model=DeprecatedResponse,
    summary="Deprecated — use /sentiment/insight",
)
async def news_deprecated(
    response: Response,
    symbol: str = Query(..., min_length=1, max_length=32),
) -> DeprecatedResponse:
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = f'<{REPLACEMENT_PATH}>; rel="successor-version"'
    return DeprecatedResponse(
        deprecated=True,
        message=DEPRECATION_MESSAGE,
        replacement=REPLACEMENT,
        symbol=symbol.strip().upper(),
    )


# ── Deprecated: /sentiment/score ─────────────────────────────────────────────
# Replaced by `/sentiment/insight`. The old controller scored eight freshly
# scraped headlines on every request, which meant the same stock could answer
# differently depending on when you asked. Its body is kept below, commented
# out — the stored path and the live fallback both live in
# `app/modules/sentiment/service.py::get_insight` now.
#
# @router.get("/score", response_model=SentimentScoreResponse)
# async def score(
#     symbol: str = Query(..., min_length=1, max_length=32),
#     interval: Interval = Query("1d"),
#     period: Period = Query("2y"),
# ) -> SentimentScoreResponse:
#     from app.modules.analytics import service as analytics
#     from app.modules.market_data import service as market_data
#
#     clean = symbol.strip().upper()
#
#     headlines = await service.get_headlines(clean)
#     news_sent = service.get_sentiment_score(headlines)
#
#     candles = await market_data.get_history(clean, interval, period)
#     df = analytics.candles_to_df(candles)
#     df = analytics.add_indicators(df)
#     tech_sent = service.compute_technical_sentiment(df)
#
#     return SentimentScoreResponse(
#         symbol=clean,
#         finbert_available=service.FINBERT_OK,
#         news=NewsSentiment(**news_sent),
#         technical=TechnicalSentiment(
#             score=tech_sent["score"],
#             label=tech_sent["label"],
#             raw_score=tech_sent["raw_score"],
#             signals=[
#                 TechnicalSignal(name=n, tone=t, message=m, weight=w)
#                 for (n, t, m, w) in tech_sent["signals"]
#             ],
#         ),
#     )


@router.get(
    "/score",
    response_model=DeprecatedResponse,
    summary="Deprecated — use /sentiment/insight",
)
async def score_deprecated(
    response: Response,
    symbol: str = Query(..., min_length=1, max_length=32),
) -> DeprecatedResponse:
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = f'<{REPLACEMENT_PATH}>; rel="successor-version"'
    return DeprecatedResponse(
        deprecated=True,
        message=DEPRECATION_MESSAGE,
        replacement=REPLACEMENT,
        symbol=symbol.strip().upper(),
    )
