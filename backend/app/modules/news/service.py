"""News scraper core — collect articles for one stock and store them.

Four design decisions here are load-bearing, and all of them come from measured
behaviour of the upstream source rather than assumption.

**1. One stock at a time.**
Scraping is driven one symbol per invocation (`scrape(symbol, days)`). A 3-year
backfill is ~1,095 requests for a single stock, and Google throttles by IP — so
a run that spans all 86 symbols invites the 503 that ends the whole crawl,
whereas a single-symbol run either completes or fails cleanly and can simply be
re-run. Dedup makes re-running free, so a partial run never wastes work.

**2. One-day windows, not one wide window.**
A single request covering a whole week returns only the most recent handful of
results — Google silently truncates, with no error. Measured on Reliance over
one week:

    1 x 7-day window   ->   9 articles  ( 25% recall)
    7 x 1-day windows  ->  32 articles  (100% recall)

So `_collect_for_rung` walks backwards one day at a time. Overlapping windows
are free because inserts are deduplicated on `(content_hash, symbol)`.

**3. Abort loudly when the source is down.**
`fetch_articles` raises `SourceUnavailable` instead of returning `[]` when it
cannot read the feed at all, and the run stops on the first such window. A
previous version returned `[]` on network failure, which made a Google outage
look exactly like a quiet news day — a backfill would store three years of
nothing and report success.

**4. Bodies are a recent-window luxury.**
No feed carries article text, so a body costs a second HTTP request per article.
Backfilling bodies for 3 years x 86 stocks would mean six figures of publisher
requests and an IP ban. So `body` is filled only for articles published within
`BODY_FILL_DAYS` — which is to say, by the weekly refresh, and never by the
backfill. A NULL body is a normal state, not a failure.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import cast

import httpx
from sqlalchemy import Table, bindparam, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.news_db import NewsSessionLocal
from app.modules.news.extractor import EXTRACTOR_OK, fetch_body
from app.modules.news.models import NewsArticle
from app.modules.news.sources import (
    RawArticle,
    SourceUnavailable,
    configure_rate_limit,
    fetch_articles,
    normalise_title,
    preflight,
)
from app.modules.news.symbols import Target, by_symbol

logger = logging.getLogger(__name__)

MAX_DAYS = 3650

# Measured on Google News RSS: 8-32 workers returned zero throttling responses.
DEFAULT_CONCURRENCY = 8

# Global requests/second cap — 20/minute. Google answers a throttled request
# with a small HTML "Sorry..." page and a 503, and the block survives for 25+
# hours once triggered (measured: an earlier run at ~25 req/s blocked this IP from
# 2026-10-03 16:20 IST until switching networks on 2026-10-04). The old default
# of 1.5 req/s was 90/min, which is faster than the ceiling we want to respect.
#
# This is the pacing that matters, not concurrency: `DEFAULT_CONCURRENCY` only
# hides per-request latency. A 3-year run is ~1,095 requests, so 20/min puts it
# at roughly 55 minutes per stock — slow on purpose, because a re-block costs
# days.
DEFAULT_REQUESTS_PER_SECOND = 20 / 60

# Only articles published inside this window get a body fetched. Set to match
# the weekly refresh interval: a 7-day run fills bodies, a 1095-day backfill
# stores headline-only rows. See module docstring §4.
BODY_FILL_DAYS = 7

# Publisher pages are fetched concurrently with the headline crawl but on their
# own hosts, so they get their own (slower) budget.
BODY_CONCURRENCY = 4
BODY_REQUESTS_PER_SECOND = 1.0

# Days fetched between commits. A 1,000-day backfill at the rate cap above takes
# ~50 minutes, so committing only at the end would throw away the whole run on a
# crash. Thirty days is ~1.5 minutes of work at that pace — small enough that
# resuming costs almost nothing, large enough that the commit overhead (one
# round trip per chunk) stays negligible.
CHECKPOINT_EVERY_DAYS = 30

# Called with each finished chunk of relevant articles; the sink is expected to
# store and commit them.
ChunkSink = Callable[[list[RawArticle]], Awaitable[None]]


class ScrapeAborted(RuntimeError):
    """The run was stopped because the upstream source failed.

    Raised instead of returning partial statistics, so no caller can mistake a
    truncated crawl for a completed one.
    """


@dataclass(slots=True)
class ScrapeStats:
    """Counters for one scrape run — surfaced by the API and used in tests."""

    symbol: str = ""
    articles_seen: int = 0
    articles_new: int = 0
    duplicates: int = 0
    rejected: int = 0
    requests: int = 0
    errors: int = 0
    bodies_stored: int = 0
    bodies_failed: int = 0
    aborted: bool = False
    per_symbol: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "articles_seen": self.articles_seen,
            "articles_new": self.articles_new,
            "duplicates": self.duplicates,
            "rejected": self.rejected,
            "requests": self.requests,
            "errors": self.errors,
            "bodies_stored": self.bodies_stored,
            "bodies_failed": self.bodies_failed,
            "aborted": self.aborted,
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


# ── Junk filters ─────────────────────────────────────────────────────────────
# Both of these were added after a live 3-day run stored 30 articles for
# RELIANCE.NS of which only ~4 were actually news. Google News matched a quoted
# company-name query against auto-generated broker quote pages, so the corpus was
# 53% templated SEO spam. Neither filter can drop a genuine story: they only
# match shapes that no editorial headline ever takes.

# Tokens that carry no identifying information, so they cannot be used alone to
# decide an article is about a company. "Reliance Industries" -> "Reliance" is
# distinctive; "State Bank of India" -> "Bank", "India" and "State" are not.
_NAME_STOPWORDS = frozenset(
    {
        "and", "the", "of", "co", "company", "corp", "corporation", "general",
        "group", "holdings", "india", "indus", "industries", "industry", "ltd",
        "limited", "national", "power", "private", "public", "financial",
        "finance", "bank", "state", "services", "limited.",
    }
)

# Templated quote and roundup pages. Each pattern requires the tell-tale pairing,
# because on its own "share price" appears in plenty of real headlines
# ("Reliance share price slips 2% after Q2 results").
#
# A tuple, not a generator: `any()` over a generator consumes it, which would
# leave every call after the first matching nothing at all.
_BOILERPLATE_PATTERNS = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\boption chain\b",
        r"\bshare price\b.*\b(live nse|live bse|upstox|moneycontrol|chart)\b",
        r"\b(live nse|live bse)\b.*\bstock price\b",
        r"\bshare price today\b",
        r"\bstock price\s*&\s*chart\b",
        r"\bindex (price )?today\b",
        r"\blive level\b",
        r"\btop \d+ .*(stocks|companies|equities|funds)\b",
        r"\blist of .*(stocks|companies|equities)\b",
        r"\bbest .*(stocks|companies|equities)\b",
        r"\bstocks to buy\b",
    )
)


def is_boilerplate(article: RawArticle) -> bool:
    """True for templated quote/roundup pages that are not news.

    These are worthless as model input and poison the sentiment corpus: a page
    titled "Oberoi Realty Share Price - Upstox" is emitted once per listed stock
    and matched almost any quoted-company query.
    """
    haystack = f"{article.title} {article.source or ''}"
    return any(pattern.search(haystack) for pattern in _BOILERPLATE_PATTERNS)


def _distinctive_tokens(target: Target) -> tuple[str, ...]:
    """Identifying words from the company name, stopwords removed.

    Lets "Reliance's Andhra Pradesh CBG push" match "Reliance Industries"
    without letting "State Bank of India" match on the word "State".
    """
    words = re.split(r"[^A-Za-z]+", f"{target.display_name} {target.nse_name}")
    tokens: list[str] = []
    for word in words:
        token = word.lower()
        if len(token) >= 5 and token not in _NAME_STOPWORDS and token not in tokens:
            tokens.append(token)
    return tuple(tokens)


def is_relevant(article: RawArticle, target: Target) -> bool:
    """Reject articles that mention the symbol without being about it.

    Bare-symbol searches are noisy in a specific, measured way: querying `ACC`
    returns American College of Cardiology and Saudi cricket fixtures. Rung 1
    and 2 of the ladder use the company name so they rarely need this; rung 3
    (bare symbol) does. We accept the article only if the company name, the
    official NSE name, or a distinctive token from either appears in the headline.
    """
    haystack = f"{article.title} {article.source or ''}".lower()

    name = target.display_name.lower()
    if len(name) >= 6 and name in haystack:
        return True

    official = target.nse_name.lower()
    if len(official) >= 6 and official in haystack:
        return True

    # Distinctive-token fallback. Catches the possessive and inflected forms a
    # strict full-name substring test would drop: "Reliance's Andhra Pradesh CBG
    # push", "Hindustan Unilever Q3". Case-insensitive with word boundaries,
    # because at this point the token is already specific to one company.
    for token in _distinctive_tokens(target):
        if re.search(rf"\b{re.escape(token)}", haystack):
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
    stats: ScrapeStats,
) -> list[tuple[int, str]]:
    """Bulk-insert articles, skipping ones already stored for this symbol.

    Returns `(id, url)` for each row that was actually inserted, which is what the
    body pass needs — duplicates are skipped here, so re-running never re-fetches
    a body it already has.
    """
    if not articles:
        return []

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
                "body": None,
                "source": article.source,
                "published_at": article.published_at,
                "url": article.url,
                "content_hash": content_hash(title),
                "fetched_at": datetime.now(UTC),
            }
        )

    if not rows:
        return []

    # ON CONFLICT DO NOTHING -> re-running the scraper is free and idempotent.
    statement = (
        pg_insert(NewsArticle)
        .values(rows)
        .on_conflict_do_nothing(constraint="uq_news_article_hash_symbol")
        .returning(NewsArticle.id, NewsArticle.url)
    )
    result = await session.execute(statement)
    inserted = [(row[0], row[1] or "") for row in result.fetchall()]

    stats.articles_new += len(inserted)
    stats.duplicates += len(rows) - len(inserted)
    return inserted


async def fill_bodies(
    client: httpx.AsyncClient,
    session: AsyncSession,
    inserted: list[tuple[int, str]],
    stats: ScrapeStats,
) -> None:
    """Fetch and store article text for freshly inserted, recent articles.

    Only rows whose `published_at` falls inside `BODY_FILL_DAYS` are eligible,
    which is what keeps the 3-year backfill headline-only while the weekly
    refresh fills in text. See module docstring §4.

    A failed extraction leaves `body` NULL and bumps `bodies_failed`; it never
    aborts the run. Publishers block, paywall and 404 constantly, and losing one
    article body is not a reason to lose a whole stock.
    """
    if not inserted:
        return
    if not EXTRACTOR_OK:
        logger.warning("news: bs4/lxml unavailable — storing headline-only rows")
        return

    # `published_at` is not part of RETURNING, so re-read it for the rows just
    # written. Restricted to `inserted` ids, so this stays cheap.
    ids = [article_id for article_id, _url in inserted]
    stored = await session.execute(
        select(NewsArticle.id, NewsArticle.url, NewsArticle.published_at).where(
            NewsArticle.id.in_(ids)
        )
    )

    cutoff = datetime.now(UTC) - timedelta(days=BODY_FILL_DAYS)
    candidates = [
        (row_id, url)
        for row_id, url, published_at in stored.all()
        if url and published_at is not None and published_at >= cutoff
    ]

    if not candidates:
        logger.info(
            "news: no articles inside the %d-day body window — skipped", BODY_FILL_DAYS
        )
        return

    logger.info("news: fetching bodies for %d articles", len(candidates))
    semaphore = asyncio.Semaphore(BODY_CONCURRENCY)

    async def one(article_id: int, url: str) -> tuple[int, str | None]:
        async with semaphore:
            return article_id, await fetch_body(client, url)

    results = await asyncio.gather(*(one(row_id, url) for row_id, url in candidates))

    updates = [
        {"article_id": article_id, "body": body}
        for article_id, body in results
        if body is not None
    ]
    if updates:
        # A Core update on the table, not an ORM one. The ORM's "bulk update by
        # primary key" path demands the dict be keyed by the real PK column name
        # (`id`) while rejecting `id` as an explicit bindparam name, and it also
        # refuses to run alongside a WHERE clause without `synchronize_session`.
        # Going straight to the Table avoids all three constraints and issues a
        # single executemany instead of one round trip per article.
        table = cast(Table, NewsArticle.__table__)
        await session.execute(
            update(table)
            .where(table.c.id == bindparam("article_id"))
            .values({"body": bindparam("body")}),
            updates,
        )
        stats.bodies_stored += len(updates)
    stats.bodies_failed += len(results) - len(updates)

    logger.info(
        "news: bodies stored %d, unavailable %d",
        stats.bodies_stored,
        stats.bodies_failed,
    )


async def scrape_symbol(
    client: httpx.AsyncClient,
    target: Target,
    days: int,
    end: datetime | None = None,
    stats: ScrapeStats | None = None,
    semaphore: asyncio.Semaphore | None = None,
    abort: asyncio.Event | None = None,
    on_chunk: ChunkSink | None = None,
    skip_days: frozenset[date] = frozenset(),
) -> list[RawArticle]:
    """Collect articles for one symbol, one checkpoint-sized chunk at a time.

    Walks backwards one day at a time — see the module docstring for why that
    matters. Returns everything collected, so tests can assert on it without
    touching the database.

    **Chunked, not all-at-once.** Days are processed in `CHECKPOINT_EVERY_DAYS`
    groups and each finished group is handed to `on_chunk`, which stores and
    commits it. A 3-year run is ~55 minutes at the measured rate, so a single
    commit at the end means a crash discards the entire run; committing every 30
    days bounds that loss to ~1.5 minutes of work.

    **The query ladder is now per chunk.** Previously each rung was tried across
    all 1,095 days before moving to the next, which meant one noisy stock could
    never fall back for its quiet days. Trying rung 1 for a chunk, then rung 2 for
    *that same chunk*, keeps recall identical while making progress incremental.

    `skip_days` lets a resumed run bypass day-windows that already have stored
    articles, so restarting after a crash costs only the days never reached.

    Stops descending the ladder once `abort` is set, so a dead source costs one
    failed window rather than three.
    """
    stats = stats if stats is not None else ScrapeStats()
    stop_at = end or datetime.now(UTC)
    sem = semaphore or asyncio.Semaphore(1)
    halt = abort or asyncio.Event()
    collected: list[RawArticle] = []

    for chunk in _day_chunks(days, stop_at, skip_days):
        if halt.is_set():
            break

        for terms in target.query_terms():
            if halt.is_set():
                break

            windows = [(start, stop) for start, stop, _ in chunk]
            day_articles = await _collect_for_windows(
                client, terms, windows, stats, sem, halt
            )
            if halt.is_set():
                break
            if not day_articles:
                continue

            # Every rung is filtered, including the quoted-phrase ones.
            #
            # This used to skip filtering whenever the query pinned a quoted
            # phrase, on the reasoning that Google had already entity-filtered it.
            # A live run disproved that: `"Reliance Industries" NSE` returned Upstox
            # quote templates for unrelated companies ("Oberoi Realty Share
            # Price", "Amber Enterprises Share Price"), because those
            # auto-generated pages match the phrase and rank well. Of 30 articles
            # stored for RELIANCE.NS only ~4 were news — 16 were boilerplate. A
            # quoted phrase constrains the query; it does not constrain results.
            relevant = [
                a for a in day_articles if not is_boilerplate(a) and is_relevant(a, target)
            ]
            stats.rejected += len(day_articles) - len(relevant)
            if not relevant:
                continue

            collected.extend(relevant)
            if on_chunk is not None:
                await on_chunk(relevant)
            break  # this chunk is satisfied; do not widen the ladder for it

    return collected


def _day_chunks(
    days: int,
    stop_at: datetime,
    skip_days: frozenset[date] = frozenset(),
) -> list[list[tuple[datetime, datetime, date]]]:
    """Split the look-back window into backwards chunks of 1-day windows.

    Each entry is `(start, end, date)`. Chunks nearer `stop_at` come first, so an
    interrupted run has covered the most recent news before it reaches back into
    history.
    """
    windows: list[tuple[datetime, datetime, date]] = []
    for offset in range(days):
        end = stop_at - timedelta(days=offset)
        start = end - timedelta(days=1)
        if start.date() in skip_days:
            continue
        windows.append((start, end, start.date()))

    return [
        windows[i : i + CHECKPOINT_EVERY_DAYS]
        for i in range(0, len(windows), CHECKPOINT_EVERY_DAYS)
    ]


async def _collect_for_windows(
    client: httpx.AsyncClient,
    terms: str,
    windows: list[tuple[datetime, datetime]],
    stats: ScrapeStats,
    semaphore: asyncio.Semaphore,
    abort: asyncio.Event,
) -> list[RawArticle]:
    """Fetch one query across a set of 1-day windows, concurrently.

    Windows are independent, so they are dispatched together and bounded by a
    shared semaphore rather than awaited one at a time. `abort` is checked before
    every request so that the first dead window stops the remaining ones from
    being fired at a source that is already refusing us.
    """
    if not windows:
        return []

    stats.requests += len(windows)

    async def guarded(start: datetime, end: datetime) -> list[RawArticle]:
        # The semaphore MUST be held around each request. Without it, gather()
        # would fire every window in the chunk at once, queueing far more sockets
        # than the pool has connections.
        async with semaphore:
            if abort.is_set():
                return []
            return await fetch_articles(client, terms, start, end)

    results = await asyncio.gather(
        *(guarded(start, end) for start, end in windows),
        return_exceptions=True,
    )

    found: list[RawArticle] = []
    for (start, end), result in zip(windows, results, strict=True):
        if isinstance(result, SourceUnavailable):
            # Loud, immediate, and fatal to the run. See module docstring §3.
            abort.set()
            stats.errors += 1
            stats.aborted = True
            logger.error("news: source failed on window %s..%s: %s", start, end, result)
            return []
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
    symbol: str,
    days: int = 7,
    requests_per_second: float = DEFAULT_REQUESTS_PER_SECOND,
) -> ScrapeStats:
    """Scrape news for **one** stock over the last `days` days and store it.

    `days` is the look-back window, sliced one day at a time because a single
    wide query silently truncates (see module docstring §2). Use 7 for the
    weekly refresh and 1095 for the one-time 3-year backfill.

    Article bodies are fetched only for articles published within
    `BODY_FILL_DAYS`, so a 7-day run fills text and a 1095-day run stores
    headlines alone.

    Raises `ValueError` for a bad symbol or window, and `ScrapeAborted` if
    Google News stops answering — never returns partial statistics that could
    be mistaken for a finished crawl.

    `requests_per_second` is the real safety valve; it is not a parameter the
    caller needs in normal use, and defaults to the measured-safe value.
    """
    if days < 1 or days > MAX_DAYS:
        raise ValueError(f"days must be between 1 and {MAX_DAYS}")

    target = by_symbol(symbol)
    if target is None:
        raise ValueError(f"'{symbol}' is not in the news scrape universe")

    configure_rate_limit(requests_per_second)

    stats = ScrapeStats(symbol=target.symbol)
    abort = asyncio.Event()
    semaphore = asyncio.Semaphore(DEFAULT_CONCURRENCY)

    logger.info(
        "news: %s over %d days (~%d requests, checkpoint every %d days)",
        target.symbol,
        days,
        days * len(target.query_terms()),
        CHECKPOINT_EVERY_DAYS,
    )

    # One session for the whole run, committed once per chunk. Progress is
    # therefore visible in the database *while* the crawl is still going, and a
    # crash costs at most CHECKPOINT_EVERY_DAYS of fetching rather than all of
    # it. Holding one session open is safe because every commit ends its
    # transaction, so a failure never leaves a half-written chunk behind.
    async with NewsSessionLocal() as session:

        async def checkpoint(chunk: list[RawArticle]) -> None:
            """Store and commit one chunk of already-filtered articles."""
            await store_articles(session, target, chunk, stats)
            await session.commit()
            print(
                f"  [*] Committed checkpoint for {target.symbol}: "
                f"{stats.articles_new:,} new stored ({stats.duplicates:,} dupes, {stats.articles_seen:,} seen)",
                flush=True,
            )
            logger.info(
                "news: %s checkpoint committed — %d new so far (%d seen)",
                target.symbol,
                stats.articles_new,
                stats.articles_seen,
            )

        limits = httpx.Limits(
            max_connections=DEFAULT_CONCURRENCY * 2,
            max_keepalive_connections=DEFAULT_CONCURRENCY,
        )
    async with httpx.AsyncClient(
            follow_redirects=True, limits=limits, timeout=25.0
        ) as client:
            # Ask for one real feed before committing to ~1,000 requests. A
            # blocked IP should cost two requests, not a whole backfill.
            try:
                await preflight(client)
            except SourceUnavailable as exc:
                stats.aborted = True
                stats.errors += 1
                logger.error("news: preflight failed, not starting: %s", exc)
                raise ScrapeAborted(f"google news is not responding: {exc}") from exc

            articles = await scrape_symbol(
                client,
                target,
                days,
                stats=stats,
                semaphore=semaphore,
                abort=abort,
                on_chunk=checkpoint,
            )

            if stats.aborted:
                raise ScrapeAborted(
                    f"google news stopped responding partway through {target.symbol}; "
                    "everything collected before the failure is already stored. "
                    "Re-run the same command to resume."
                )

            if not articles:
                logger.info("news: %s - 0 articles in %d days", target.symbol, days)
            else:
                stats.per_symbol[target.symbol] = stats.articles_new
                logger.info(
                    "news: %s stored %d new (%d dupes) of %d seen",
                    target.symbol,
                    stats.articles_new,
                    stats.duplicates,
                    stats.articles_seen,
                )

    logger.info(
        "news: done - %d stored, %d duplicates, %d rejected, %d errors",
        stats.articles_new,
        stats.duplicates,
        stats.rejected,
        stats.errors,
    )
    return stats


async def distinct_symbols() -> list[str]:
    """Every symbol currently stored in the news database, sorted."""
    async with NewsSessionLocal() as session:
        rows = await session.execute(select(NewsArticle.symbol).distinct())
        return sorted({row[0] for row in rows.all() if row[0]})


async def scrape_all(
    days: int = 7,
    requests_per_second: float = DEFAULT_REQUESTS_PER_SECOND,
) -> ScrapeStats:
    """Refresh news for every symbol already stored in the news database.

    Queries `news_articles` for the distinct set of symbols, then runs the
    normal single-symbol scrape for each of them in sequence. `days` is the
    look-back window (default 30) — small enough for a weekly refresh, large
    enough to backfill gaps.

    A failure on one symbol is logged and skipped so one bad stock cannot
    abort the whole batch. Returns aggregate counters across all symbols.
    """
    if days < 1 or days > MAX_DAYS:
        raise ValueError(f"days must be between 1 and {MAX_DAYS}")

    symbols = await distinct_symbols()
    if not symbols:
        logger.info("news: scrape_all found no stored symbols, nothing to do")
        return ScrapeStats(symbol="ALL")

    logger.info("news: scrape_all refreshing %d symbols over %d days", len(symbols), days)

    aggregate = ScrapeStats(symbol="ALL")
    for idx, symbol in enumerate(symbols, 1):
        print(f"[{idx}/{len(symbols)}] Refreshing {symbol} ({days} days)...", flush=True)
        try:
            stats = await scrape(symbol=symbol, days=days, requests_per_second=requests_per_second)
            print(
                f"       -> Stored {stats.articles_new:,} new articles "
                f"({stats.duplicates:,} duplicates, {stats.articles_seen:,} seen)",
                flush=True,
            )
        except (ValueError, ScrapeAborted) as exc:
            aggregate.errors += 1
            print(f"       -> Skipped/Failed: {exc}", flush=True)
            logger.error("news: scrape_all failed for %s: %s", symbol, exc)
            continue
        aggregate.articles_seen += stats.articles_seen
        aggregate.articles_new += stats.articles_new
        aggregate.duplicates += stats.duplicates
        aggregate.rejected += stats.rejected
        aggregate.requests += stats.requests
        aggregate.errors += stats.errors
        aggregate.bodies_stored += stats.bodies_stored
        aggregate.bodies_failed += stats.bodies_failed
        aggregate.per_symbol[symbol] = stats.articles_new
        if stats.aborted:
            aggregate.aborted = True

    logger.info(
        "news: scrape_all done - %d symbols, %d new articles, %d errors",
        len(symbols),
        aggregate.articles_new,
        aggregate.errors,
    )
    return aggregate
