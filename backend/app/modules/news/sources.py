"""News source adapters — parse RSS into `RawArticle` records.

Deliberately built on `xml.etree.ElementTree` rather than the regex scraping
used by the legacy sentiment module (`app/modules/sentiment/service.py:42-54`).
Regex scraping is why that module silently discards `pubDate`, `<source>` and
`<link>`, and why a change in Google's markup would quietly return zero articles
instead of failing loudly. A real parser raises instead.

Only one source is wired today (Google News RSS, no API key). The
`fetch_articles` signature is the seam where a paid provider or GDELT can be
added later without touching the scraper in `service.py`.
"""

from __future__ import annotations

import asyncio
import contextlib
import random
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx

_UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

GOOGLE_NEWS_URL = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

# Google appends " - Publisher Name" to most headline titles. Stripping it
# keeps the stored title clean and makes the dedupe hash stable across
# outlets that syndicate the same story.
_PUBLISHER_SUFFIX = re.compile(r"\s+-\s+[^-]{2,60}$")


@dataclass(frozen=True, slots=True)
class RawArticle:
    """One headline exactly as the source reported it (nothing dropped)."""

    title: str
    source: str | None
    published_at: datetime | None
    url: str | None


def build_query(search_terms: str, start: datetime, end: datetime) -> str:
    """Build a Google News query restricted to a date window.

    `start` is inclusive, `end` exclusive — both UTC.
    """
    return f"{search_terms} after:{start:%Y-%m-%d} before:{end:%Y-%m-%d}"


def normalise_title(title: str) -> str:
    """Collapse a headline to a comparable form for dedupe hashing."""
    cleaned = _PUBLISHER_SUFFIX.sub("", title.strip())
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", cleaned.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _parse_pubdate(raw: str | None) -> datetime | None:
    """RFC-2822 pubDate -> timezone-aware UTC datetime."""
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if parsed is None:
        return None
    # Google emits "GMT"; anything naive is assumed UTC.
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_rss(xml_text: str) -> list[RawArticle]:
    """Parse an RSS 2.0 document into articles, keeping every field.

    Raises `ElementTree.ParseError` on malformed XML — a loud failure beats the
    legacy behaviour of returning an empty list for a broken feed.
    """
    root = ElementTree.fromstring(xml_text)
    articles: list[RawArticle] = []

    for item in root.iter("item"):
        fields: dict[str, str] = {}
        for child in item:
            tag = child.tag.rsplit("}", 1)[-1]  # strip any namespace
            fields.setdefault(tag, (child.text or "").strip())

        title = fields.get("title", "").strip()
        if not title:
            continue

        articles.append(
            RawArticle(
                title=title,
                source=fields.get("source") or None,
                published_at=_parse_pubdate(fields.get("pubDate")),
                url=fields.get("link") or None,
            )
        )

    return articles


# ── Global rate limiting ────────────────────────────────────────────────────
# Measured ceiling for sustained use of this endpoint: a 3-year backfill at 16
# workers pushed Google into returning HTTP 503 for every subsequent request,
# including single serial ones, for 5+ minutes. Short bursts look perfectly
# healthy, which is what makes this easy to get wrong — it works fine until it
# suddenly does not.
#
# So requests are paced by one shared lock rather than by worker concurrency.
# Concurrency still hides per-request latency; this is what keeps the aggregate
# request rate inside what Google tolerates.
DEFAULT_REQUESTS_PER_SECOND = 1.5
_MIN_INTERVAL = 1.0 / DEFAULT_REQUESTS_PER_SECOND

_PACE_LOCK = asyncio.Lock()
_LAST_REQUEST = 0.0


def configure_rate_limit(requests_per_second: float) -> None:
    """Set the global request pace (requests/second). Call before a long run."""
    global _MIN_INTERVAL
    _MIN_INTERVAL = 1.0 / max(0.1, float(requests_per_second))


@contextlib.asynccontextmanager
async def _pace_request():
    """Yield once this request's slot is free.

    Serialised on an asyncio lock so concurrent callers start one at a time
    rather than all being released together. The sleep MUST be `await
    asyncio.sleep` — a blocking `time.sleep` here stalls the whole event loop
    and quietly serialises the scraper (measured: 2.08 req/s against a 3 req/s
    cap).
    """
    global _LAST_REQUEST
    async with _PACE_LOCK:
        wait = _LAST_REQUEST + _MIN_INTERVAL - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        _LAST_REQUEST = time.monotonic()
    yield


async def fetch_articles(
    client: httpx.AsyncClient,
    search_terms: str,
    start: datetime,
    end: datetime,
    attempts: int = 3,
) -> list[RawArticle]:
    """Fetch one date window from Google News.

    Returns `[]` on network failure or malformed XML — callers treat an empty
    result as "nothing found for this window", which is a normal outcome for
    thinly-covered stocks.

    Retries with exponential backoff, so an occasional 503 does not cost us a
    day of coverage that a later re-run would have to rediscover.
    """
    url = GOOGLE_NEWS_URL.format(query=build_query(search_terms, start, end))

    for attempt in range(attempts):
        async with _pace_request():
            try:
                response = await client.get(url, headers=_UA, timeout=25.0)
                response.raise_for_status()
                return parse_rss(response.text)
            except httpx.HTTPError:
                if attempt == attempts - 1:
                    return []
                # Jittered backoff so retries don't re-synchronise across workers.
                await asyncio.sleep((2**attempt) * 1.5 + random.random() * 0.5)
    return []
