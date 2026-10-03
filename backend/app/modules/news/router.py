"""News collection API.

Phase 1 is collection + storage only. Sentiment scoring is intentionally absent
and will land as a separate module reading from these tables.

All endpoints require authentication, matching every other router in the app.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.deps import get_current_user
from app.core.news_db import NewsSessionLocal, init_news_db
from app.modules.news import symbols as symbols_mod
from app.modules.news.models import NewsArticle
from app.modules.news.schemas import (
    NewsArticleListResponse,
    NewsArticleOut,
    NewsCoverageResponse,
    ScrapeRequest,
    ScrapeResult,
)
from app.modules.news.service import MAX_DAYS, scrape

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/news",
    tags=["news"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/scrape",
    response_model=ScrapeResult,
    summary="Scrape news headlines into the news database",
    description=(
        "Collects Google News headlines per symbol and stores them in the "
        "**separate news database** (`SV_DATABASE_NEWS_URL`).\n\n"
        "**How `days` works:** the look-back window is sliced **one day at a "
        "time**. A single wide query silently truncates — measured on RELIANCE, "
        "one 7-day query returned 9 headlines versus 32 from seven 1-day "
        "queries (25% vs 100% recall). Expect roughly `days x symbols` requests.\n\n"
        "**Idempotent:** duplicates are skipped on `(content_hash, symbol)`, so "
        "re-running never double-stores. Re-scrape a 7-day window after a 3-year "
        "backfill to pick up anything missed.\n\n"
        "Use `days=7` for the weekly refresh or `days=1095` for the one-time "
        "3-year backfill. This is a synchronous, long-running call — prefer "
        "`max_symbols` for large windows."
    ),
)
async def run_scrape(payload: ScrapeRequest) -> ScrapeResult:
    started = time.perf_counter()
    try:
        stats = await scrape(
            days=payload.days,
            symbols=payload.symbols,
            max_symbols=payload.max_symbols,
            concurrency=payload.concurrency,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("news scrape failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"News scrape failed: {exc}",
        ) from exc

    return ScrapeResult.from_stats(stats, round(time.perf_counter() - started, 2))


@router.get(
    "/articles",
    response_model=NewsArticleListResponse,
    summary="Read stored headlines for one symbol",
)
async def list_articles(
    symbol: str = Query(..., min_length=1, max_length=32, description="e.g. RELIANCE.NS"),
    limit: int = Query(50, ge=1, le=500),
    days: int | None = Query(
        None,
        ge=1,
        le=MAX_DAYS,
        description="Optional look-back window; omit for everything stored.",
    ),
) -> NewsArticleListResponse:
    target = symbols_mod.by_symbol(symbol)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{symbol}' is not in the news scrape universe.",
        )

    query = select(NewsArticle).where(NewsArticle.symbol == target.symbol)
    if days is not None:
        since = datetime.now(UTC) - timedelta(days=days)
        query = query.where(NewsArticle.published_at >= since)

    query = query.order_by(NewsArticle.published_at.desc().nullslast()).limit(limit)

    async with NewsSessionLocal() as session:
        rows = list((await session.execute(query)).scalars())

    return NewsArticleListResponse(
        symbol=target.symbol,
        count=len(rows),
        articles=[NewsArticleOut.model_validate(row, from_attributes=True) for row in rows],
    )


@router.get(
    "/coverage",
    response_model=NewsCoverageResponse,
    summary="Show the scrape universe and how much has been stored",
)
async def coverage() -> NewsCoverageResponse:
    await init_news_db()

    async with NewsSessionLocal() as session:
        total = await session.scalar(select(func.count()).select_from(NewsArticle)) or 0
        grouped = await session.execute(
            select(NewsArticle.symbol, func.count())
            .group_by(NewsArticle.symbol)
            .order_by(func.count().desc())
        )
        per_symbol = {symbol: count for symbol, count in grouped.all()}

    return NewsCoverageResponse(
        universe=symbols_mod.coverage(),
        total_articles=int(total),
        symbols_covered=len(per_symbol),
        articles_per_symbol=per_symbol,
    )
