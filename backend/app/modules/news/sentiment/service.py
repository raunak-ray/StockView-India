"""Score stored articles with FinBERT, roll the results up, and serve them.

Two halves that never meet:

  * ``score_pending`` / ``aggregate_symbols`` are **offline batch** functions.
    They run from `scripts/score_sentiment.py`, hold the model in memory, and
    are free to take minutes.
  * ``get_symbol_sentiment`` / ``get_history`` / ``get_ranking`` are **request
    path** functions. They only ever SELECT. No model, no network, no AI work
    during a user request — that is the whole point of this phase.

The legacy live path (`app/modules/sentiment/service.py::get_headlines` +
`get_sentiment_score`) is what used to run on every page view: 8 headlines
scraped and pushed through the model each time. It is superseded by these
tables.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast

import numpy as np
from sqlalchemy import Row, delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.db import SessionLocal
from app.core.news_db import NewsSessionLocal
from app.modules.news.models import NewsArticle
from app.modules.news.sentiment.models import (
    NewsArticleSentiment,
    NewsSentimentPeriod,
    StockNewsSentiment,
)

logger = logging.getLogger(__name__)

MODEL_VERSION = "prosusai-finbert"
KEYWORD_VERSION = "keyword_only"

# Matches the existing blend so results stay consistent with what the project
# already produced (sentiment/service.py:198).
FINBERT_WEIGHT = 0.70
KEYWORD_WEIGHT = 0.30

# BULISH / BEARISH / NEUTRAL thresholds, kept identical to the live path.
BULLISH_AT = 0.08
BEARISH_AT = -0.08

LABEL_FOR_SIGN = {"positive": "BULLISH", "negative": "BEARISH", "neutral": "NEUTRAL"}

TOP_N_EXTREMES = 5

# ── Chart periods ───────────────────────────────────────────────────────────
# The four windows the sentiment-vs-price chart offers. `days` drives the
# look-back; `bucket` is how the series is grouped, and it gets coarser with the
# window so the payload stays chart-sized — 3 years of daily sentiment is ~780
# points per stock, which is noise on a chart and slow to serialise.
#
# Bucket sizes are in days. Sentiment buckets are calendar-aligned from today
# backwards rather than anchored to month starts, so every window ends on the
# same "now" and the four cards are directly comparable.
PERIODS: dict[str, dict[str, Any]] = {
    "1m": {"label": "1M", "days": 30, "bucket": 1},
    "3m": {"label": "3M", "days": 91, "bucket": 1},
    "1y": {"label": "1Y", "days": 365, "bucket": 7},
    "3y": {"label": "3Y", "days": 1095, "bucket": 30},
}

# yfinance only offers these look-backs, so the longest period is fetched with
# the smallest one that covers it and then sliced per window.
_PRICE_PERIOD = "5y"

# asyncpg caps bind parameters at **32,767 per statement** — half of Postgres's
# own 65,535 limit, and the number that actually bites. A multi-VALUES insert
# costs one parameter per column per row, so the row ceiling is
# limit / column_count. Derived rather than hard-coded so adding a column to the
# model cannot silently push a chunk back over the edge: this bug cost a full
# scoring run, because the failure aborted the whole insert and left 0 rows.
_INSERT_MAX_PARAMS = 30_000
_INSERT_CHUNK_ROWS = max(
    1, _INSERT_MAX_PARAMS // max(1, len(NewsArticleSentiment.__table__.c))
)


@dataclass(slots=True)
class ScoreResult:
    """Counters from one scoring run."""

    unscored_seen: int = 0
    scored: int = 0
    skipped_existing: int = 0
    keyword_fallback: int = 0
    batch_size: int = 32

    def as_dict(self) -> dict[str, int]:
        return {
            "unscored_seen": self.unscored_seen,
            "scored": self.scored,
            "skipped_existing": self.skipped_existing,
            "keyword_fallback": self.keyword_fallback,
        }


def _pipeline():
    """Load FinBERT, reusing the app's existing singleton loader.

    Deliberately not reimplemented: the model is ~440 MB and `_load_finbert`
    already keeps one process-wide instance. Importing it also means the
    capability flag (`FINBERT_OK`) and the cache-on-disk behaviour stay in one
    place.
    """
    from app.modules.sentiment.service import _keyword_score, _load_finbert

    return _load_finbert(), _keyword_score


def blend(finbert_signed: float, keyword: float) -> float:
    """Combine the model score with the legacy keyword score."""
    return round(FINBERT_WEIGHT * finbert_signed + KEYWORD_WEIGHT * keyword, 6)


def label_for(score: float) -> str:
    if score > BULLISH_AT:
        return "BULLISH"
    if score < BEARISH_AT:
        return "BEARISH"
    return "NEUTRAL"


async def score_pending(
    symbol: str | None = None,
    limit: int | None = None,
    batch_size: int = 32,
) -> ScoreResult:
    """Score every stored article that has no sentiment row yet.

    Resumable and idempotent: articles already present in
    `news_article_sentiment` are excluded, so re-running costs nothing and a
    half-finished run continues where it stopped.
    """
    pipe, keyword_score = _pipeline()
    model_version = MODEL_VERSION if pipe is not None else KEYWORD_VERSION
    if pipe is None:
        logger.warning("news sentiment: FinBERT unavailable — keyword scores only")

    print("[*] Checking for unscored articles in news database...", flush=True)
    async with NewsSessionLocal() as news:
        query = (
            select(
                NewsArticle.id,
                NewsArticle.symbol,
                NewsArticle.title,
                NewsArticle.published_at,
            )
            .outerjoin(
                NewsArticleSentiment,
                NewsArticleSentiment.article_id == NewsArticle.id,
            )
            .where(NewsArticleSentiment.article_id.is_(None))
        )
        if symbol:
            query = query.where(NewsArticle.symbol == symbol.upper())
        query = query.order_by(NewsArticle.id)
        if limit:
            query = query.limit(limit)

        pending = list((await news.execute(query)).all())

    result = ScoreResult(unscored_seen=len(pending), batch_size=batch_size)
    if not pending:
        print("[*] No pending articles found — all stored articles are already scored.", flush=True)
        logger.info("news sentiment: nothing pending")
        return result

    print(f"[*] Found {len(pending):,} pending articles to score.", flush=True)
    if pipe is not None:
        print(f"[*] Running FinBERT inference in batches of {batch_size}...", flush=True)
    else:
        print("[*] FinBERT unavailable — running keyword scoring fallback...", flush=True)

    # Model scoring is CPU-bound and synchronous, so it runs off the event loop
    # in one go rather than per-article.
    scored_rows, fallbacks = await _run_model(pending, pipe, keyword_score, batch_size)
    result.keyword_fallback = fallbacks

    print(f"[*] Committing {len(scored_rows):,} scored articles to news database...", flush=True)
    async with NewsSessionLocal() as news:
        # Chunked because a single multi-VALUES insert is one bind parameter per
        # column per row. Each sentiment row has 12 columns, so the whole corpus
        # in one statement needs 12 x N parameters — and Postgres/asyncpg caps
        # that at 65,535. Measured: 6,158 articles produced 73,896 parameters and
        # the insert failed outright, so nothing was scored at all. 5,000 rows per
        # statement stays well under the cap with room for the columns to grow.
        written = 0
        for offset in range(0, len(scored_rows), _INSERT_CHUNK_ROWS):
            chunk = scored_rows[offset : offset + _INSERT_CHUNK_ROWS]
            await news.execute(
                pg_insert(NewsArticleSentiment)
                .values(chunk)
                .on_conflict_do_nothing(index_elements=["article_id"])
            )
            written += len(chunk)
        await news.commit()
    result.scored = written

    logger.info(
        "news sentiment: scored %d articles (%d keyword fallback) as %s",
        result.scored,
        fallbacks,
        model_version,
    )
    return result


async def _run_model(
    pending: list[Row],
    pipe,
    keyword_score,
    batch_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """Push titles through FinBERT in batches. Returns (rows, fallback_count)."""
    import anyio.to_thread

    return await anyio.to_thread.run_sync(
        _score_sync, pending, pipe, keyword_score, batch_size
    )


def _score_sync(
    pending: list[Row],
    pipe,
    keyword_score,
    batch_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """Blocking worker: batch-inference then keyword blend.

    Batching is the single biggest win here — the legacy path ran one forward
    pass per headline with no `batch_size`. Measured on CPU: 9.4 ms/article at
    batch 32 versus roughly 120 ms unbatched.
    """
    titles = [row.title for row in pending]
    keywords = [keyword_score(title) for title in titles]

    fallbacks = 0
    if pipe is None:
        fallbacks = len(pending)
        outputs = []
    else:
        # Batch inference through FinBERT with live progress
        outputs = []
        try:
            from tqdm import tqdm
            pbar = tqdm(
                total=len(titles),
                desc="Scoring headlines",
                unit="article",
                dynamic_ncols=True,
            )
        except ImportError:
            pbar = None

        for offset in range(0, len(titles), batch_size):
            chunk = titles[offset : offset + batch_size]
            batch_res = pipe(chunk, truncation=True, max_length=256, top_k=None)
            outputs.extend(batch_res)
            if pbar is not None:
                pbar.update(len(chunk))

        if pbar is not None:
            pbar.close()

    rows: list[dict[str, Any]] = []
    for index, (article_id, symbol, title, published_at) in enumerate(pending):
        kw = float(keywords[index])

        if pipe is None or index >= len(outputs):
            # No model: record the keyword result honestly rather than passing
            # it off as FinBERT.
            signed = kw
            pos = neu = neg = 0.0
            label = "positive" if kw > 0 else "negative" if kw < 0 else "neutral"
            confidence = abs(kw)
            version = KEYWORD_VERSION
        else:
            # A single string yields one dict; a list of strings yields one
            # entry per input. Normalise both to a list of dicts.
            entry = outputs[index]
            scored = entry if isinstance(entry, list) else [entry]
            probs = {str(p["label"]).lower(): float(p["score"]) for p in scored}
            pos = probs.get("positive", 0.0)
            neu = probs.get("neutral", 0.0)
            neg = probs.get("negative", 0.0)
            label = max(probs, key=lambda k: probs[k]) if probs else "neutral"
            signed = {"positive": 1.0, "negative": -1.0}.get(label, 0.0) * probs.get(
                label, 0.0
            )
            confidence = probs.get(label, 0.0)
            version = MODEL_VERSION

        rows.append(
            {
                "article_id": article_id,
                "symbol": symbol,
                "published_at": published_at,
                "finbert_pos": round(pos, 6),
                "finbert_neu": round(neu, 6),
                "finbert_neg": round(neg, 6),
                "finbert_label": label,
                "keyword_score": round(kw, 6),
                "final_score": blend(float(signed), kw),
                "confidence": round(confidence, 6),
                "model_version": version,
            }
        )

    return rows, fallbacks


async def aggregate_symbols(symbol: str | None = None) -> dict[str, Any]:
    """Rebuild `stock_news_sentiment` (main DB) and the daily rollup.

    Recomputed from scratch each run rather than incremented, so it can never
    drift out of sync with the article-level scores.
    """
    print("[*] Fetching scored sentiment rows from news database...", flush=True)
    async with NewsSessionLocal() as news:
        query = (
            select(
                NewsArticleSentiment.article_id,
                NewsArticleSentiment.symbol,
                NewsArticleSentiment.final_score,
                NewsArticleSentiment.finbert_label,
                NewsArticleSentiment.confidence,
                NewsArticleSentiment.published_at,
                NewsArticleSentiment.model_version,
            )
            .order_by(NewsArticleSentiment.article_id)
        )
        if symbol:
            query = query.where(NewsArticleSentiment.symbol == symbol.upper())

        scored = list((await news.execute(query)).all())

        # Titles are only needed for the extremes, so fetch them alongside.
        extremes_rows = (
            await news.execute(
                select(
                    NewsArticleSentiment.symbol,
                    NewsArticleSentiment.final_score,
                    NewsArticle.title,
                    NewsArticle.source,
                    NewsArticle.published_at,
                    NewsArticle.url,
                )
                .join(NewsArticle, NewsArticle.id == NewsArticleSentiment.article_id)
                .where(
                    NewsArticleSentiment.symbol == symbol.upper()
                    if symbol
                    else NewsArticleSentiment.symbol.is_not(None)
                )
            )
        ).all()

    by_symbol: dict[str, list[Row]] = {}
    for row in scored:
        by_symbol.setdefault(row[1], []).append(row)

    extremes: dict[str, list[dict[str, Any]]] = {}
    for sym, score, title, src, published, url in extremes_rows:
        extremes.setdefault(sym, []).append(
            {
                "title": title,
                "score": round(float(score), 4),
                "source": src,
                "published_at": published.isoformat() if published else None,
                "url": url,
            }
        )

    summaries: list[dict[str, Any]] = []
    daily: dict[tuple[str, date], dict[str, Any]] = {}

    for sym, entries in by_symbol.items():
        scores = np.array([e[2] for e in entries], dtype=float)
        labels = [e[3] for e in entries]
        confs = np.array([e[4] for e in entries], dtype=float)
        mean = float(scores.mean()) if len(scores) else 0.0

        published = [e[5] for e in entries if e[5] is not None]
        versions = {e[6] for e in entries}
        version = MODEL_VERSION if MODEL_VERSION in versions else KEYWORD_VERSION

        summaries.append(
            {
                "symbol": sym,
                "score": round(mean, 6),
                "label": label_for(mean),
                "article_count": len(entries),
                "pos_count": sum(1 for lb in labels if lb == "positive"),
                "neu_count": sum(1 for lb in labels if lb == "neutral"),
                "neg_count": sum(1 for lb in labels if lb == "negative"),
                "avg_confidence": round(float(confs.mean()), 6) if len(confs) else 0.0,
                "window_start": min(published) if published else None,
                "window_end": max(published) if published else None,
                "top_positive": [],
                "top_negative": [],
                "model_version": version,
                "updated_at": datetime.now(UTC),
            }
        )

        for entry, label in zip(entries, labels, strict=True):
            day = (entry[5] or datetime.now(UTC)).date()
            bucket = daily.setdefault(
                (sym, day),
                {
                    "symbol": sym,
                    "day": day,
                    "article_count": 0,
                    "_sum": 0.0,
                    "pos_count": 0,
                    "neu_count": 0,
                    "neg_count": 0,
                    "model_version": version,
                },
            )
            bucket["article_count"] += 1
            bucket["_sum"] += float(entry[2])
            bucket["pos_count"] += 1 if label == "positive" else 0
            bucket["neu_count"] += 1 if label == "neutral" else 0
            bucket["neg_count"] += 1 if label == "negative" else 0

    for summary in summaries:
        items = sorted(extremes.get(summary["symbol"], []), key=lambda x: x["score"])
        summary["top_positive"] = items[-TOP_N_EXTREMES:][::-1]
        summary["top_negative"] = items[:TOP_N_EXTREMES]

    # Period rows replace the old per-day table. The in-memory `daily` rollup is
    # still the convenient intermediate — it is grouped by exact date, so any
    # period window can be carved out of it without another query — but it is
    # never persisted.
    today = datetime.now(UTC).date()
    period_values: list[dict[str, Any]] = []

    for sym in {b["symbol"] for b in daily.values()}:
        by_day = {b["day"]: b for b in daily.values() if b["symbol"] == sym}
        version = (
            MODEL_VERSION
            if MODEL_VERSION in {b["model_version"] for b in by_day.values()}
            else KEYWORD_VERSION
        )
        for key, cfg in PERIODS.items():
            since = today - timedelta(days=cfg["days"])
            window = [b for day, b in by_day.items() if since <= day <= today]
            if not window:
                continue

            count = sum(b["article_count"] for b in window)
            weighted = sum(b["_sum"] for b in window)
            mean = weighted / count if count else 0.0

            # Bucket the window so "did coverage warm or cool?" is answerable.
            step = cfg["bucket"]
            buckets: dict[date, dict[str, float]] = {}
            for b in window:
                slot = today - timedelta(days=(today - b["day"]).days // step * step)
                agg = buckets.setdefault(
                    slot, {"sum": 0.0, "n": 0.0}
                )
                agg["sum"] += b["_sum"]
                agg["n"] += b["article_count"]

            means = [v["sum"] / v["n"] for v in buckets.values() if v["n"]]
            change = (means[-1] - means[0]) if len(means) > 1 else 0.0

            period_values.append(
                {
                    "symbol": sym,
                    "period": key,
                    "days": cfg["days"],
                    "score": round(mean, 6),
                    "label": label_for(mean),
                    "article_count": count,
                    "pos_count": sum(b["pos_count"] for b in window),
                    "neu_count": sum(b["neu_count"] for b in window),
                    "neg_count": sum(b["neg_count"] for b in window),
                    "avg_confidence": 0.0,
                    "window_start": datetime.combine(min(b["day"] for b in window),
                                                    datetime.min.time(), tzinfo=UTC),
                    "window_end": datetime.combine(max(b["day"] for b in window),
                                                   datetime.max.time().replace(microsecond=0),
                                                   tzinfo=UTC),
                    "sentiment_change": round(change, 6),
                    "model_version": version,
                    "updated_at": datetime.now(UTC),
                }
            )

    print(f"[*] Correlating sentiment with stock prices for {len(by_symbol)} symbols...", flush=True)
    prices = await _fetch_prices(sorted({b["symbol"] for b in daily.values()}))
    # `period_row`, not `row`: `row` is already bound to a query Row earlier in
    # this function and rebinding it to a dict breaks the inferred type.
    for period_row in period_values:
        window_closes = prices.get(period_row["symbol"], {}).get(period_row["period"])
        if window_closes:
            first, last = window_closes[0], window_closes[-1]
            period_row["price_start"] = first
            period_row["price_end"] = last
            period_row["price_change_pct"] = (
                round((last - first) / first * 100, 4) if first else None
            )

    print(
        f"[*] Committing {len(summaries)} stock summaries and {len(period_values)} period cards to main database...",
        flush=True,
    )
    async with SessionLocal() as app:
        if summaries:
            await app.execute(
                pg_insert(StockNewsSentiment)
                .values(summaries)
                .on_conflict_do_update(
                    constraint="stock_news_sentiment_pkey",
                    set_={
                        "score": pg_insert(StockNewsSentiment)
                        .excluded.score,
                        "label": pg_insert(StockNewsSentiment).excluded.label,
                        "article_count": pg_insert(StockNewsSentiment)
                        .excluded.article_count,
                        "pos_count": pg_insert(StockNewsSentiment).excluded.pos_count,
                        "neu_count": pg_insert(StockNewsSentiment).excluded.neu_count,
                        "neg_count": pg_insert(StockNewsSentiment).excluded.neg_count,
                        "avg_confidence": pg_insert(StockNewsSentiment)
                        .excluded.avg_confidence,
                        "window_start": pg_insert(StockNewsSentiment)
                        .excluded.window_start,
                        "window_end": pg_insert(StockNewsSentiment).excluded.window_end,
                        "top_positive": pg_insert(StockNewsSentiment)
                        .excluded.top_positive,
                        "top_negative": pg_insert(StockNewsSentiment)
                        .excluded.top_negative,
                        "model_version": pg_insert(StockNewsSentiment)
                        .excluded.model_version,
                        "updated_at": pg_insert(StockNewsSentiment).excluded.updated_at,
                    },
                )
            )
            await app.commit()

        # Delete rows for symbols that no longer have any scored articles.
        #
        # The upsert above only ever touches symbols present in the corpus, so a
        # symbol whose articles were deleted keeps its old summary forever —
        # and `/news/sentiment/ranking` then lists it with a score computed from
        # headlines that no longer exist. That is the same class of bug as
        # reporting NEUTRAL for a stock we never measured: a confident-looking
        # number about nothing.
        live_symbols = {s["symbol"] for s in summaries}
        if live_symbols:
            await app.execute(
                delete(StockNewsSentiment).where(
                    StockNewsSentiment.symbol.not_in(live_symbols)
                )
            )
            await app.execute(
                delete(NewsSentimentPeriod).where(
                    NewsSentimentPeriod.symbol.not_in(live_symbols)
                )
            )
            await app.commit()

        if period_values:
            # Primary key is (symbol, period), so the constraint name is what the
            # upsert targets. No separate UniqueConstraint is declared on the
            # model — naming the PK constraint directly avoids the duplicate
            # unique index the old daily table carried.
            await app.execute(
                pg_insert(NewsSentimentPeriod)
                .values(period_values)
                .on_conflict_do_update(
                    constraint="news_sentiment_period_pkey",
                    set_={
                        "days": pg_insert(NewsSentimentPeriod).excluded.days,
                        "score": pg_insert(NewsSentimentPeriod).excluded.score,
                        "label": pg_insert(NewsSentimentPeriod).excluded.label,
                        "article_count": pg_insert(NewsSentimentPeriod).excluded.article_count,
                        "pos_count": pg_insert(NewsSentimentPeriod).excluded.pos_count,
                        "neu_count": pg_insert(NewsSentimentPeriod).excluded.neu_count,
                        "neg_count": pg_insert(NewsSentimentPeriod).excluded.neg_count,
                        "avg_confidence": pg_insert(NewsSentimentPeriod).excluded.avg_confidence,
                        "window_start": pg_insert(NewsSentimentPeriod).excluded.window_start,
                        "window_end": pg_insert(NewsSentimentPeriod).excluded.window_end,
                        "sentiment_change": pg_insert(NewsSentimentPeriod)
                        .excluded.sentiment_change,
                        "price_start": pg_insert(NewsSentimentPeriod).excluded.price_start,
                        "price_end": pg_insert(NewsSentimentPeriod).excluded.price_end,
                        "price_change_pct": pg_insert(NewsSentimentPeriod)
                        .excluded.price_change_pct,
                        "model_version": pg_insert(NewsSentimentPeriod).excluded.model_version,
                        "updated_at": pg_insert(NewsSentimentPeriod).excluded.updated_at,
                    },
                )
            )
            await app.commit()

    logger.info(
        "news sentiment: aggregated %d symbols, %d period rows",
        len(summaries),
        len(period_values),
    )
    return {
        "symbols": len(summaries),
        "period_rows": len(period_values),
        "priced_symbols": sum(1 for r in period_values if r["price_start"] is not None),
    }



# ── Price ───────────────────────────────────────────────────────────────────


async def _fetch_price_closes(symbol: str) -> dict[date, float]:
    """Daily close prices for one symbol, keyed by date.

    Reuses the market-data module so sentiment charts and the price charts on
    the stock page cannot disagree — both read the same Redis-cached yfinance
    series. A failure returns an empty mapping rather than raising: sentiment is
    the primary signal here, and a missing quote must not blank the sentiment
    side of the comparison.
    """
    from app.modules.market_data import service as market

    try:
        # `period` is a Literal on the market-data side, so the constant is typed
        # rather than left as a bare str for mypy.
        candles = await market.get_history(
            symbol, interval="1d", period=cast(Any, _PRICE_PERIOD)
        )
    except Exception as exc:  # noqa: BLE001 - upstream is best-effort by design
        logger.warning("news sentiment: price fetch failed for %s: %s", symbol, exc)
        return {}

    closes: dict[date, float] = {}
    for candle in candles:
        stamp = candle.get("time")
        close = candle.get("close")
        if not stamp or close is None:
            continue
        try:
            closes[datetime.fromisoformat(str(stamp)).date()] = float(close)
        except ValueError:
            continue
    return closes


async def _fetch_prices(symbols: list[str]) -> dict[str, dict[str, list[float]]]:
    """First/last close per (symbol, period) — what the period cards store.

    One fetch per symbol, sliced four ways, rather than four fetches.
    Concurrent with bounded concurrency (5) so 28+ symbols fetch in seconds.
    """
    today = datetime.now(UTC).date()
    out: dict[str, dict[str, list[float]]] = {}
    if not symbols:
        return out

    try:
        from tqdm import tqdm
        pbar = tqdm(total=len(symbols), desc="Fetching stock prices", unit="stock", dynamic_ncols=True)
    except ImportError:
        pbar = None

    sem = asyncio.Semaphore(5)

    async def _fetch_one(sym: str) -> tuple[str, dict[date, float]]:
        async with sem:
            res = await _fetch_price_closes(sym)
            if pbar is not None:
                pbar.update(1)
            return sym, res

    results = await asyncio.gather(*[_fetch_one(s) for s in symbols])
    if pbar is not None:
        pbar.close()

    for symbol, closes in results:
        if not closes:
            continue
        by_period: dict[str, list[float]] = {}
        for key, cfg in PERIODS.items():
            since = today - timedelta(days=cfg["days"])
            window = [closes[day] for day in sorted(closes) if since <= day <= today]
            if window:
                by_period[key] = window
        out[symbol] = by_period
    return out


async def _fetch_series_closes(symbol: str) -> dict[date, float]:
    """Full close series for chart alignment (see ``get_trend``)."""
    return await _fetch_price_closes(symbol)


def _bucket_key(day: date, step: int, today: date) -> date:
    """Align a date to its bucket, counting backwards from `today`.

    Counting backwards rather than forwards from an epoch keeps every period
    ending on the same day, so the 1M/3M/1Y/3Y cards line up on the right edge.
    """
    if step <= 1:
        return day
    return today - timedelta(days=(today - day).days // step * step)


# ── Request path: SELECT only, never runs the model ──────────────────────────


async def get_symbol_sentiment(symbol: str) -> dict[str, Any] | None:
    """The stored summary for one stock, or None when there is no coverage.

    Returning None is deliberate. A stock with no articles must NOT be reported
    as "NEUTRAL" — that would claim we measured something neutral when we
    actually found nothing, which is precisely the failure mode of the old
    8-headline live scrape.
    """
    clean = symbol.strip().upper()
    async with SessionLocal() as app:
        row = (
            await app.execute(
                select(StockNewsSentiment).where(StockNewsSentiment.symbol == clean)
            )
        ).scalar_one_or_none()

    if row is None or not row.article_count:
        return None
    return {
        "symbol": row.symbol,
        "score": round(float(row.score), 4),
        "label": row.label,
        "coverage": "available",
        "article_count": row.article_count,
        "counts": {
            "positive": row.pos_count,
            "neutral": row.neu_count,
            "negative": row.neg_count,
        },
        "avg_confidence": round(float(row.avg_confidence), 4),
        "window": {
            "start": row.window_start,
            "end": row.window_end,
        },
        "top_positive": row.top_positive or [],
        "top_negative": row.top_negative or [],
        "model_version": row.model_version,
        "updated_at": row.updated_at,
    }


async def get_trend(symbol: str) -> dict[str, Any]:
    """Everything the sentiment-vs-price chart needs, in one payload.

    Returns all four periods (1M / 3M / 1Y / 3Y) at once, because a chart with a
    period switcher would otherwise need four round trips and render four times.
    Each period carries:

      * a headline summary from the materialised ``news_sentiment_period`` table
        (score, label, counts, window, sentiment change, price change)
      * a bucketed ``series`` — sentiment and close price on the same axis, so
        the frontend can plot two lines against one x-axis with no client-side
        date joining

    The series is derived live from ``news_article_sentiment`` rather than
    stored, because that is where the truth is: re-bucketing is a GROUP BY over
    one symbol's rows, and storing a parallel copy would only create a second
    thing to fall out of date.

    Periods with no coverage are still returned, with ``article_count: 0`` and an
    empty series, so the frontend can render an inactive tab instead of handling
    a missing key.
    """
    clean = symbol.strip().upper()
    today = datetime.now(UTC).date()

    async with SessionLocal() as app:
        stored = (
            await app.execute(
                select(NewsSentimentPeriod).where(NewsSentimentPeriod.symbol == clean)
            )
        ).scalars()
    cards = {row.period: row for row in stored}

    # Sentiment rows for the widest window only, then sliced per period.
    widest = max(cfg["days"] for cfg in PERIODS.values())
    since_widest = today - timedelta(days=widest)

    async with NewsSessionLocal() as news:
        rows = (
            await news.execute(
                select(
                    NewsArticleSentiment.published_at,
                    NewsArticleSentiment.final_score,
                    NewsArticleSentiment.finbert_label,
                    NewsArticleSentiment.confidence,
                ).where(
                    NewsArticleSentiment.symbol == clean,
                    NewsArticleSentiment.published_at.is_not(None),
                    NewsArticleSentiment.published_at >= datetime.combine(
                        since_widest, datetime.min.time(), tzinfo=UTC
                    ),
                )
            )
        ).all()

    closes = await _fetch_series_closes(clean)

    periods: dict[str, Any] = {}
    for key, cfg in PERIODS.items():
        since = today - timedelta(days=cfg["days"])
        step = cfg["bucket"]

        buckets: dict[date, dict[str, float]] = {}
        for published_at, score, label, confidence in rows:
            day = published_at.date()
            if not (since <= day <= today):
                continue
            slot = _bucket_key(day, step, today)
            agg = buckets.setdefault(slot, {"sum": 0.0, "n": 0.0, "conf": 0.0, "pos": 0.0})
            agg["sum"] += float(score)
            agg["n"] += 1
            agg["conf"] += float(confidence)
            agg["pos"] += 1 if label == "positive" else 0

        # Price is bucketed on the same axis; a bucket with no quote (a weekend,
        # a holiday) borrows the most recent earlier close so the line does not
        # break on every market holiday.
        price_by_slot: dict[date, float] = {}
        last_close: float | None = None
        for day in sorted(closes):
            if day > today:
                continue
            last_close = closes[day]
            if since <= day <= today:
                price_by_slot[_bucket_key(day, step, today)] = last_close

        series = []
        for slot in sorted(set(buckets) | set(price_by_slot)):
            # `point`, not `agg` — the caller already binds `agg` to a non-optional
            # dict and mypy rejects the rebind to Optional.
            point = buckets.get(slot)
            series.append(
                {
                    "date": slot.isoformat(),
                    "sentiment": round(point["sum"] / point["n"], 4)
                    if point and point["n"]
                    else None,
                    "article_count": int(point["n"]) if point else 0,
                    "avg_confidence": round(point["conf"] / point["n"], 4)
                    if point and point["n"]
                    else 0.0,
                    "pos_count": int(point["pos"]) if point else 0,
                    "close": price_by_slot.get(slot) or last_close,
                }
            )

        card = cards.get(key)
        # `card and card.x` reads as "card exists and has a value", but mypy
        # narrows `card` and not its attribute, so spell the attribute check out.
        card_start = card.window_start if card else None
        card_end = card.window_end if card else None
        periods[key] = {
            "label": cfg["label"],
            "days": cfg["days"],
            "granularity": {1: "day", 7: "week", 30: "month"}.get(step, f"{step}d"),
            "sentiment": {
                "score": round(float(card.score), 4) if card else None,
                "label": card.label if card else "NO_DATA",
                "article_count": card.article_count if card else 0,
                "pos_count": card.pos_count if card else 0,
                "neu_count": card.neu_count if card else 0,
                "neg_count": card.neg_count if card else 0,
                "avg_confidence": round(float(card.avg_confidence), 4) if card else 0.0,
                "change": round(float(card.sentiment_change), 4) if card else None,
                "window_start": card_start.isoformat() if card_start else None,
                "window_end": card_end.isoformat() if card_end else None,
            },
            "price": {
                "start": card.price_start if card else None,
                "end": card.price_end if card else None,
                "change_pct": round(float(card.price_change_pct), 3)
                if card is not None and card.price_change_pct is not None
                else None,
                "currency": "INR",
            },
            "series": series,
        }

    model_version = next((r.model_version for r in stored), MODEL_VERSION)
    return {
        "symbol": clean,
        "model_version": model_version,
        "generated_at": datetime.now(UTC).isoformat(),
        "as_of": today.isoformat(),
        "has_coverage": any(p["sentiment"]["article_count"] > 0 for p in periods.values()),
        "periods": periods,
    }


async def get_history(symbol: str, days: int) -> list[dict[str, Any]]:
    """Daily sentiment series for the history chart, oldest first.

    Kept for the older `/history` endpoint. Reads article-level scores rather
    than a rollup table — the per-day table it used to read has been replaced by
    `news_sentiment_period`, and this view is derived from the same source of
    truth.
    """
    clean = symbol.strip().upper()
    since = datetime.now(UTC).date() - timedelta(days=days)

    async with NewsSessionLocal() as news:
        rows = (
            await news.execute(
                select(
                    NewsArticleSentiment.published_at,
                    NewsArticleSentiment.final_score,
                    NewsArticleSentiment.finbert_label,
                )
                .where(
                    NewsArticleSentiment.symbol == clean,
                    NewsArticleSentiment.published_at.is_not(None),
                )
                .order_by(NewsArticleSentiment.published_at)
            )
        ).all()

    buckets: dict[date, dict[str, Any]] = {}
    for published_at, score, label in rows:
        day = published_at.date()
        if day < since:
            continue
        agg = buckets.setdefault(
            day, {"mean_score": 0.0, "article_count": 0, "pos_count": 0, "neu_count": 0, "neg_count": 0}
        )
        agg["mean_score"] += float(score)
        agg["article_count"] += 1
        agg[f"{'pos' if label == 'positive' else 'neu' if label == 'neutral' else 'neg'}_count"] += 1

    return [
        {
            "day": day,
            "article_count": agg["article_count"],
            "mean_score": round(agg["mean_score"] / agg["article_count"], 4),
            "pos_count": agg["pos_count"],
            "neu_count": agg["neu_count"],
            "neg_count": agg["neg_count"],
        }
        for day, agg in sorted(buckets.items())
    ]


async def get_ranking(limit: int = 50) -> list[dict[str, Any]]:
    """Every scored stock, most bullish first — feeds the chatbot shortlist."""
    async with SessionLocal() as app:
        rows = (
            await app.execute(
                select(StockNewsSentiment)
                .where(StockNewsSentiment.article_count > 0)
                .order_by(StockNewsSentiment.score.desc())
                .limit(limit)
            )
        ).scalars()

    return [
        {
            "symbol": row.symbol,
            "score": round(float(row.score), 4),
            "label": row.label,
            "article_count": row.article_count,
        }
        for row in rows
    ]


async def get_scored_articles(
    symbol: str, limit: int = 20, days: int | None = None
) -> list[dict[str, Any]]:
    """Dated, sourced, scored headlines — the stored replacement for the live feed."""
    clean = symbol.strip().upper()
    async with NewsSessionLocal() as news:
        query = (
            select(
                NewsArticle.id,
                NewsArticle.title,
                NewsArticle.source,
                NewsArticle.published_at,
                NewsArticle.url,
                NewsArticleSentiment.final_score,
                NewsArticleSentiment.finbert_label,
            )
            .join(
                NewsArticleSentiment,
                NewsArticleSentiment.article_id == NewsArticle.id,
            )
            .where(NewsArticleSentiment.symbol == clean)
            .order_by(NewsArticle.published_at.desc().nullslast())
            .limit(limit)
        )
        if days:
            since = datetime.now(UTC) - timedelta(days=days)
            query = query.where(NewsArticle.published_at >= since)

        rows = (await news.execute(query)).all()

    return [
        {
            "id": r[0],
            "title": r[1],
            "source": r[2],
            "published_at": r[3],
            "url": r[4],
            "score": round(float(r[5]), 4),
            "label": LABEL_FOR_SIGN.get(str(r[6]).lower(), "NEUTRAL"),
        }
        for r in rows
    ]


def _empty_period_card(key: str) -> dict[str, Any]:
    """A period we have no rows for.

    Returned instead of omitting the key so the frontend always finds the four
    periods it knows about and can render an inactive tab instead of a hole.
    """
    cfg = PERIODS[key]
    return {
        "period": key,
        "title": cfg["label"],
        "days": cfg["days"],
        "available": False,
        "score": None,
        "label": "NO_DATA",
        "article_count": 0,
        "pos_count": 0,
        "neu_count": 0,
        "neg_count": 0,
        "avg_confidence": 0.0,
        "sentiment_change": None,
        "window_start": None,
        "window_end": None,
        "price_start": None,
        "price_end": None,
        "price_change_pct": None,
    }


def _labelled_extremes(items: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Add a label to the stored extremes.

    The rows in `stock_news_sentiment.top_positive` / `top_negative` were
    written before the label existed — they carry the score and nothing else.
    The tone follows the score, so it is derived here rather than making the
    whole corpus re-aggregate for one field.
    """
    out: list[dict[str, Any]] = []
    for item in items or []:
        try:
            score = float(item.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        out.append({**item, "label": label_for(score)})
    return out


async def get_symbol_bundle(
    symbol: str, article_limit: int = 12
) -> dict[str, Any] | None:
    """Everything stored for one symbol, in a single call.

    Three reads and no work: the per-stock summary and the four period cards
    live in the main database, the scored headlines live in the news database.

    Returns None when the stock has no stored sentiment at all. The caller
    then falls back to the live path — "no coverage" and "the news was neutral"
    are different claims, and only one of them is true for a stock we never
    scraped.
    """
    clean = symbol.strip().upper()

    async with SessionLocal() as app:
        summary = (
            await app.execute(
                select(StockNewsSentiment).where(StockNewsSentiment.symbol == clean)
            )
        ).scalar_one_or_none()
        period_rows = (
            await app.execute(
                select(NewsSentimentPeriod).where(NewsSentimentPeriod.symbol == clean)
            )
        ).scalars().all()

    if summary is None or not summary.article_count:
        return None

    periods: dict[str, Any] = {key: _empty_period_card(key) for key in PERIODS}
    for row in period_rows:
        card = periods.get(row.period)
        if card is None:
            continue
        card.update(
            {
                "available": True,
                "score": round(float(row.score), 4),
                "label": row.label,
                "article_count": row.article_count,
                "pos_count": row.pos_count,
                "neu_count": row.neu_count,
                "neg_count": row.neg_count,
                "avg_confidence": round(float(row.avg_confidence), 4),
                "sentiment_change": round(float(row.sentiment_change), 4),
                "window_start": row.window_start.isoformat()
                if row.window_start
                else None,
                "window_end": row.window_end.isoformat() if row.window_end else None,
                "price_start": row.price_start,
                "price_end": row.price_end,
                "price_change_pct": round(float(row.price_change_pct), 3)
                if row.price_change_pct is not None
                else None,
            }
        )

    articles = await get_scored_articles(clean, limit=article_limit)

    return {
        "symbol": summary.symbol,
        "score": round(float(summary.score), 4),
        "label": summary.label,
        "article_count": summary.article_count,
        "counts": {
            "positive": summary.pos_count,
            "neutral": summary.neu_count,
            "negative": summary.neg_count,
        },
        "avg_confidence": round(float(summary.avg_confidence), 4),
        "window": {
            "start": summary.window_start,
            "end": summary.window_end,
        },
        "periods": periods,
        "articles": articles,
        "top_positive": _labelled_extremes(summary.top_positive),
        "top_negative": _labelled_extremes(summary.top_negative),
        "model_version": summary.model_version,
        "updated_at": summary.updated_at.isoformat() if summary.updated_at else None,
    }


async def scoring_status() -> dict[str, Any]:
    """How much of the corpus has been scored — drives the CLI --status flag."""
    async with NewsSessionLocal() as news:
        total = await news.scalar(select(func.count()).select_from(NewsArticle))
        scored = await news.scalar(select(func.count()).select_from(NewsArticleSentiment))
        versions = (
            await news.execute(
                select(
                    NewsArticleSentiment.model_version,
                    func.count(),
                ).group_by(NewsArticleSentiment.model_version)
            )
        ).all()

    async with SessionLocal() as app:
        summaries = await app.scalar(select(func.count()).select_from(StockNewsSentiment))
        periods = await app.scalar(select(func.count()).select_from(NewsSentimentPeriod))

    return {
        "articles_total": int(total or 0),
        "articles_scored": int(scored or 0),
        "articles_pending": int(total or 0) - int(scored or 0),
        "symbols_summarised": int(summaries or 0),
        "period_rows": int(periods or 0),
        "model_versions": {str(v): int(c) for v, c in versions},
    }
