"""API for stored news sentiment.

Replaces the live flow: nothing here scrapes or runs FinBERT on a user request.
Every endpoint is a SELECT against the pre-computed tables.

Endpoints are namespaced under `/news/sentiment` rather than folded into the
existing `/sentiment` router — the old live endpoints stay in place until the
frontend is migrated, so nothing regresses for existing pages.
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user
from app.modules.news.sentiment import service
from app.modules.news.sentiment.schemas import (
    DailySentimentPoint,
    ExtremesHeadline,
    RankingEntry,
    RankingOut,
    ScoredArticleListOut,
    ScoredArticleOut,
    ScoreRunOut,
    ScoringStatusOut,
    SentimentCounts,
    SentimentHistoryOut,
    SentimentWindow,
    StockSentimentOut,
    TrendOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/news/sentiment",
    tags=["news-sentiment"],
    dependencies=[Depends(get_current_user)],
)

NO_COVERAGE = "none"
AVAILABLE = "available"


def _not_in_universe(symbol: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"'{symbol}' is not in the news scrape universe.",
    )


@router.get(
    "/status",
    response_model=ScoringStatusOut,
    summary="How much of the corpus has been scored",
)
async def scoring_status() -> ScoringStatusOut:
    return ScoringStatusOut(**await service.scoring_status())


@router.get(
    "/ranking",
    response_model=RankingOut,
    summary="All scored stocks, most bullish first",
    description=(
        "Every stock with stored sentiment, ordered by score. Feeds a "
        "recommendation shortlist or a chatbot answer."
    ),
)
async def ranking(
    limit: int = Query(50, ge=1, le=200),
) -> RankingOut:
    rows = await service.get_ranking(limit=limit)
    return RankingOut(
        count=len(rows), ranking=[RankingEntry(**row) for row in rows]
    )


@router.get(
    "/run",
    response_model=ScoreRunOut,
    summary="Score pending articles with FinBERT, then aggregate",
    description=(
        "Offline batch operation — this is the **only** place FinBERT runs. "
        "Already-scored articles are skipped, so it is safe to re-run.\n\n"
        "Long-running for large corpora; prefer "
        "`python -m scripts.score_sentiment` for bulk runs."
    ),
)
async def run_scoring(
    symbol: str | None = Query(None, description="Restrict to one symbol."),
    limit: int | None = Query(None, ge=1, description="Cap articles scored."),
    batch_size: int = Query(32, ge=1, le=64),
    aggregate: bool = Query(True, description="Rebuild summaries afterwards."),
) -> ScoreRunOut:
    started = time.perf_counter()
    result = await service.score_pending(
        symbol=symbol, limit=limit, batch_size=batch_size
    )
    agg = await service.aggregate_symbols(symbol) if aggregate else None
    return ScoreRunOut.build(
        result.as_dict(), round(time.perf_counter() - started, 2), agg
    )


@router.get(
    "/{symbol}",
    response_model=StockSentimentOut,
    summary="Stored sentiment summary for one stock",
    description=(
        "Reads the pre-computed row from the main database — no scraping and "
        "no model inference.\n\n"
        "Returns `coverage=\"none\"` with `article_count=0` when the stock has "
        "no stored articles. That is deliberately **not** reported as NEUTRAL: "
        "\"no news found\" and \"the news was neutral\" are different claims."
    ),
)
async def symbol_sentiment(symbol: str) -> StockSentimentOut:
    data = await service.get_symbol_sentiment(symbol)
    if data is None:
        return StockSentimentOut(
            symbol=symbol.strip().upper(), coverage=NO_COVERAGE, article_count=0
        )

    return StockSentimentOut(
        symbol=data["symbol"],
        score=data["score"],
        label=data["label"],
        coverage=data["coverage"],
        article_count=data["article_count"],
        counts=SentimentCounts(**data["counts"]),
        avg_confidence=data["avg_confidence"],
        window=SentimentWindow(**data["window"]),
        top_positive=[ExtremesHeadline(**item) for item in data["top_positive"]],
        top_negative=[ExtremesHeadline(**item) for item in data["top_negative"]],
        model_version=data["model_version"],
        updated_at=data["updated_at"],
    )


@router.get(
    "/{symbol}/trend",
    response_model=TrendOut,
    summary="Sentiment vs price over 1M / 3M / 1Y / 3Y — one call, whole chart",
    description=(
        "Everything the comparison graph needs, for all four periods at once.\n\n"
        "One call rather than four because the UI has a period switcher: fetching "
        "per period means four round trips and four chances to render a "
        "half-drawn chart.\n\n"
        "Each period returns:\n"
        "* `sentiment` — the stored summary (score, label, counts, window, and "
        "`change`, the first-bucket mean minus the last)\n"
        "* `price` — first/last close and percentage change\n"
        "* `series` — sentiment and close **on a shared date axis**, so two lines "
        "plot against one x-axis with no client-side date joining\n\n"
        "Bucket size follows the window: daily for 1M/3M, weekly for 1Y, monthly "
        "for 3Y. Three years of daily sentiment is ~780 points per stock, which "
        "is noise on a chart.\n\n"
        "All four period keys are always present. A period with no coverage comes "
        "back with `article_count: 0`, `label: \"NO_DATA\"` and a null score "
        "rather than a fabricated NEUTRAL, so the frontend can render an inactive "
        "tab instead of showing a measured-looking zero."
    ),
)
async def sentiment_trend(symbol: str) -> TrendOut:
    started = time.perf_counter()
    try:
        data = await service.get_trend(symbol)
    except Exception as exc:
        logger.exception("news sentiment trend failed for %s", symbol)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Sentiment trend unavailable: {exc}",
        ) from exc

    logger.info(
        "news sentiment: trend %s in %.2fs (coverage=%s)",
        data["symbol"],
        time.perf_counter() - started,
        data["has_coverage"],
    )
    return TrendOut(**data)


@router.get(
    "/{symbol}/history",
    response_model=SentimentHistoryOut,
    summary="Daily sentiment series for the history chart",
)
async def sentiment_history(
    symbol: str,
    range_days: int = Query(365, ge=1, le=3650, alias="days"),
) -> SentimentHistoryOut:
    points = await service.get_history(symbol, range_days)
    return SentimentHistoryOut(
        symbol=symbol.strip().upper(),
        days=range_days,
        coverage=AVAILABLE if points else NO_COVERAGE,
        points=[DailySentimentPoint(**point) for point in points],
    )


@router.get(
    "/{symbol}/articles",
    response_model=ScoredArticleListOut,
    summary="Stored headlines with their stored scores",
    description=(
        "The stored replacement for the old live headline feed: dated, sourced, "
        "and scored ahead of time."
    ),
)
async def scored_articles(
    symbol: str,
    limit: int = Query(20, ge=1, le=200),
    days: int | None = Query(None, ge=1, le=3650),
) -> ScoredArticleListOut:
    rows = await service.get_scored_articles(symbol, limit=limit, days=days)
    return ScoredArticleListOut(
        symbol=symbol.strip().upper(),
        count=len(rows),
        coverage=AVAILABLE if rows else NO_COVERAGE,
        articles=[ScoredArticleOut(**row) for row in rows],
    )