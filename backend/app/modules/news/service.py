"""News scraper core — collect headlines day-by-day and store them.

Two design decisions here are load-bearing, and both come from measured
behaviour of the upstream source rather than assumption.

**1. One-day windows, not one wide window.**
A single request covering a whole week returns only the most recent handful of
results — Google silently truncates, with no error. Measured on Reliance over
one week:

    1 x 7-day window   ->   9 articles  ( 25% recall)
    7 x 1-day windows  ->  32 articles  (100% recall)

So `scrape_window` walks backwards one day at a time. The cost is a few more
requests; the benefit is that nothing is silently lost. Overlapping windows are
free because inserts are deduplicated on `(content_hash, symbol)`.

**2. Every field is kept.**
The legacy scraper (`app/modules/sentiment/service.py:42-54`) reduced each feed
item to a bare title string, discarding `pubDate`, `<source>` and `<link>`. That
is precisely why the existing app cannot date a headline, deduplicate it, or
show a history. Here the full record is persisted.

Phase 1 scope is collection and storage only — no FinBERT. Scoring is wired in
as a later phase, and deliberately not smuggled into this one.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.news_db import NewsSessionLocal
from app.modules.news.models import NewsArticle
from app.modules.news.sources import (
    RawArticle,
    configure_rate_limit,
    fetch_articles,
    normalise_title,
)
from app.modules.news.symbols import Target

logger = logging.getLogger(__name__)

MAX_DAYS = 3650

# Measured on Google News RSS: 8-32 workers returned zero throttling responses.
DEFAULT_CONCURRENCY = 12


@dataclass(slots=True)
class ScrapeStats:
    """Counters for one scrape run — surfaced by the API and useful in tests."""

    articles_seen: int = 0
    articles_new: int = 0
    duplicates: int = 0
    rejected: int = 0
    requests: int = 0
    errors: int = 0
    per_symbol: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "articles_seen": self.articles_seen,
            "articles_new": self.articles_new,
            "duplicates": self.duplicates,
            "rejected": self.rejected,
            "requests": self.requests,
            "errors": self.errors,
            "symbols_processed": len(self.per_symbol),
            "per_symbol": self.per_symbol,
        }


def content_hash(title: str) -> str:
    """sha256 of the normalised title — the dedupe key.

    Normalising before hashing means the same headline syndicated under several
    publishers collapses to one row per symbol.
    """
    normalised = normalise_title(title)
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def is_relevant(article: RawArticle, target: Target) -> bool:
    """Reject articles that mention the symbol without being about it.

    Bare-symbol searches are noisy in a specific, measured way: querying `ACC`
    returns American College of Cardiology and Saudi cricket fixtures. Rung 1
    and 2 of the ladder use the company name so they rarely need this; rung 3
    (bare symbol) does. We accept the article only if the company name, the
    official NSE name, or a distinctive symbol token appears in the headline.
    """
    haystack = f"{article.title} {article.source or ''}".lower()

    name = target.display_name.lower()
    if len(name) >= 6 and name in haystack:
        return True

    official = target.nse_name.lower()
    if len(official) >= 6 and official in haystack:
        return True

    # Bare-symbol fallback. Two guards, both necessary:
    #
    #  * case-sensitive — news outlets write tickers in caps ("HAL Q2 profit"),
    #    whereas the English word "hal" in "Hal Smith wins" must not match.
    #    Twelve of the Nifty 100 symbols are 3 letters, and two of those (BEL,
    #    HAL) are also ordinary English words.
    #  * token-boundary — prevents "ACC" matching "American College of
    #    Cardiology" style substrings.
    #
    # M&M-style symbols contain punctuation and are handled by the same guard.
    bare = target.base_symbol
    raw = f" {article.title} {article.source or ''} "
    return len(bare) >= 3 and _is_standalone(f" {bare} ", raw)


def _is_standalone(token: str, haystack: str) -> bool:
    """True when `token` appears in `haystack` bounded by non-word characters.

    Apostrophes count as part of the word, so a possessive ("ACC's president")
    is **not** a ticker mention — otherwise every English headline about
    someone called Acc or Hal would match.

    `_is_standalone(" M&M ", text)` — the `&` is treated as a boundary, so this
    matches "M&M share price" but not "M&Mx".
    """
    pattern = re.escape(token.strip())
    return re.search(rf"(?:^|[^\w&']){pattern}(?:$|[^\w&'])", haystack) is not None


async def store_articles(
    session: AsyncSession,
    target: Target,
    articles: list[RawArticle],
    query_used: str,
    stats: ScrapeStats,
) -> None:
    """Bulk-insert articles, skipping ones already stored for this symbol."""
    if not articles:
        return

    rows = []
    for article in articles:
        title = article.title.strip()
        if not title:
            stats.rejected += 1
            continue
        rows.append(
            {
                "symbol": target.symbol,
                "title": title,
                "source": article.source,
                "published_at": article.published_at,
                "url": article.url,
                "query_used": query_used[:160],
                "content_hash": content_hash(title),
                "fetched_at": datetime.now(UTC),
            }
        )

    if not rows:
        return

    # ON CONFLICT DO NOTHING -> re-running the scraper is free and idempotent.
    statement = (
        pg_insert(NewsArticle)
        .values(rows)
        .on_conflict_do_nothing(constraint="uq_news_article_hash_symbol")
        .returning(NewsArticle.id)
    )
    result = await session.execute(statement)
    inserted = len(result.fetchall())

    stats.articles_new += inserted
    stats.duplicates += len(rows) - inserted


async def scrape_symbol(
    client: httpx.AsyncClient,
    target: Target,
    days: int,
    end: datetime | None = None,
    stats: ScrapeStats | None = None,
    semaphore: asyncio.Semaphore | None = None,
) -> list[RawArticle]:
    """Collect articles for one symbol over the last `days` days.

    Walks backwards one day at a time — see the module docstring for why that
    matters. Returns the collected articles so they can be stored, or asserted
    on in tests, without touching the database.
    """
    stats = stats if stats is not None else ScrapeStats()
    stop_at = end or datetime.now(UTC)
    sem = semaphore or asyncio.Semaphore(1)

    for terms in target.query_terms():
        day_articles = await _collect_for_rung(client, terms, days, stop_at, stats, sem)
        if not day_articles:
            continue

        # A quoted-phrase query is already entity-filtered by Google: asking for
        # the exact company name returns articles *about that company*, so
        # re-filtering locally would only discard legitimate coverage. That is
        # not a theoretical risk — requiring the full "Reliance Industries"
        # phrase threw away real headlines phrased as "Reliance's Andhra
        # Pradesh CBG push" and "Nuvama retains target for Reliance stock".
        #
        # The bare-symbol rung (no quoted phrase) has no such guarantee, so it
        # is the only one that needs the local relevance check.
        if _is_precise(terms):
            return day_articles

        relevant = [a for a in day_articles if is_relevant(a, target)]
        stats.rejected += len(day_articles) - len(relevant)
        if relevant:
            return relevant

    return []


def _is_precise(terms: str) -> bool:
    """True when the query pins a quoted phrase, so results are self-filtering."""
    return '"' in terms


async def _collect_for_rung(
    client: httpx.AsyncClient,
    terms: str,
    days: int,
    stop_at: datetime,
    stats: ScrapeStats,
    semaphore: asyncio.Semaphore,
) -> list[RawArticle]:
    """Fetch one query across `days` separate 1-day windows, concurrently.

    Day windows are independent, so they are dispatched together and bounded by
    a shared semaphore rather than awaited one at a time.
    """
    windows = []
    for offset in range(days):
        end = stop_at - timedelta(days=offset)
        windows.append((end - timedelta(days=1), end))

    stats.requests += len(windows)

    async def guarded(start: datetime, end: datetime) -> list[RawArticle]:
        # The semaphore MUST be held around each request. Without it, gather()
        # would fire all `days` windows at once (1,095 for a 3-year backfill),
        # queueing tens of thousands of sockets and starving every worker.
        async with semaphore:
            return await fetch_articles(client, terms, start, end)

    results = await asyncio.gather(
        *(guarded(start, end) for start, end in windows),
        return_exceptions=True,
    )

    found: list[RawArticle] = []
    for (start, end), result in zip(windows, results, strict=True):
        if isinstance(result, BaseException):
            stats.errors += 1
            logger.warning("news: window %s..%s failed: %s", start, end, result)
            continue
        found.extend(result)

    stats.articles_seen += len(found)
    logger.info(
        "news: rung '%s' -> %d articles over %d windows",
        terms[:48],
        len(found),
        len(windows),
    )
    return found


async def scrape(
    days: int = 7,
    symbols: list[str] | None = None,
    max_symbols: int | None = None,
    concurrency: int = DEFAULT_CONCURRENCY,
    requests_per_second: float | None = None,
) -> ScrapeStats:
    """Scrape news for the target universe and store it in the news database.

    `days` is the look-back window per symbol. Day-by-day slicing inside that
    window is what makes recall complete (see module docstring).

    `concurrency` hides per-request latency; `requests_per_second` is the real
    safety valve. See `sources.configure_rate_limit` — sustained concurrency
    without a global rate cap is what provoked HTTP 503 from Google.
    """
    from app.modules.news.symbols import by_symbol
    from app.modules.news.symbols import targets as all_targets

    if days < 1 or days > MAX_DAYS:
        raise ValueError(f"days must be between 1 and {MAX_DAYS}")

    if requests_per_second is not None:
        configure_rate_limit(requests_per_second)

    selected = _select_targets(symbols, max_symbols, by_symbol, all_targets)
    stats = ScrapeStats()
    semaphore = asyncio.Semaphore(max(1, concurrency))

    logger.info(
        "news: scraping %d symbols over %d days (concurrency=%d)",
        len(selected),
        days,
        concurrency,
    )

    limits = httpx.Limits(
        max_connections=max(concurrency * 2, 10),
        max_keepalive_connections=concurrency,
    )
    async with httpx.AsyncClient(follow_redirects=True, limits=limits, timeout=25.0) as client:
        queue: asyncio.Queue[Target] = asyncio.Queue()
        for target in selected:
            queue.put_nowait(target)

        async def worker() -> None:
            while True:
                try:
                    target = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return

                try:
                    articles = await scrape_symbol(
                        client, target, days, stats=stats, semaphore=semaphore
                    )
                    if articles:
                        async with NewsSessionLocal() as session:
                            await store_articles(
                                session, target, articles, target.query_terms()[0], stats
                            )
                            await session.commit()
                        stats.per_symbol[target.symbol] = len(articles)
                        logger.info(
                            "news: %-14s %4d articles (stored total %d)",
                            target.symbol,
                            len(articles),
                            stats.articles_new,
                        )
                    else:
                        logger.info("news: %-14s   0 articles", target.symbol)
                except Exception:
                    stats.errors += 1
                    logger.exception("news: %s failed", target.symbol)
                finally:
                    queue.task_done()

        worker_count = max(1, min(concurrency, len(selected)))
        await asyncio.gather(*(worker() for _ in range(worker_count)))

    logger.info(
        "news: done - %d stored, %d duplicates, %d rejected, %d errors",
        stats.articles_new,
        stats.duplicates,
        stats.rejected,
        stats.errors,
    )
    return stats


def _select_targets(
    symbols: list[str] | None,
    max_symbols: int | None,
    by_symbol,
    all_targets,
) -> list[Target]:
    """Resolve the requested symbol list into targets, preserving universe order."""
    if symbols:
        picked = [t for t in (by_symbol(s) for s in symbols) if t is not None]
        if not picked:
            raise ValueError("None of the requested symbols are in the scrape universe")
        return picked[:max_symbols] if max_symbols else picked

    universe = all_targets()
    return universe[:max_symbols] if max_symbols else universe
