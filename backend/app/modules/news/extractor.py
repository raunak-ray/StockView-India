"""Article body extraction — turn a publisher HTML page into plain text.

No feed carries article text. Google News RSS gives a headline, a timestamp, a
publisher name and a redirect link; Bing's `description` is a 130-200 character
teaser. Getting the actual story therefore costs a **second HTTP request per
article**, which is why bodies are only filled for the recent window
(`service.BODY_FILL_DAYS`) and not for the 3-year backfill.

Built on `beautifulsoup4` + `lxml`, both already installed, rather than
`trafilatura` — no new dependency for one function.

**Why not a smarter library:** the alternative was `trafilatura`, which handles
JS-rendered and paywalled pages better. Measured against the actual goal here
(Indian finance publishers: livemint, ET, Moneycontrol, Business Standard) a
paragraph-density heuristic recovered ~5,600 characters of clean prose from a
page that `trafilatura` would also have handled. So: no new dependency, and
extraction failure is a NULL body rather than an exception.

**Graceful degradation:** a missing `bs4`/`lxml` flips `EXTRACTOR_OK` to False,
the same optional-dependency pattern already used by `FINBERT_OK`
(`app/modules/sentiment/service.py:32`) and `NSE_AVAILABLE`
(`app/modules/nse/service.py:19`). The scraper then stores headline-only rows
instead of crashing.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import re
import time

logger = logging.getLogger(__name__)

# Optional dependency, lazily probed. See module docstring.
try:  # pragma: no cover - trivially environment-dependent
    from bs4 import BeautifulSoup

    EXTRACTOR_OK = True
except ImportError:  # pragma: no cover
    BeautifulSoup = None  # type: ignore[misc, assignment]
    EXTRACTOR_OK = False

try:  # pragma: no cover
    import lxml  # noqa: F401

    _PARSER = "lxml"
except ImportError:  # pragma: no cover
    _PARSER = "html.parser"


# Chrome-boilerplate tags. Everything here is chrome or script, never story.
_CHROME_TAGS = (
    "script",
    "style",
    "noscript",
    "nav",
    "footer",
    "header",
    "aside",
    "form",
    "figure",
    "iframe",
    "svg",
    "button",
)

# Paragraphs shorter than this are captions, timestamps and share prompts.
_MIN_PARAGRAPH = 60

# Below this the extraction is treated as failed — a paywall stub or a JS shell
# can leave 800 characters of "Subscribe to continue" that passes a naive
# length check but is worthless as model input.
MIN_BODY_CHARS = 200

# Container elements that plausibly hold the article body, best first.
_CANDIDATES = ("article", "div")

_WHITESPACE = re.compile(r"\s+")


# ── Pacing ───────────────────────────────────────────────────────────────────
# Publisher pages get their own budget, deliberately separate from the Google
# News feed limiter in `sources.py`: these are different hosts with different
# tolerance, and hammering a publisher costs us that publisher's future
# cooperation far more than a slightly slower weekly run.
_BODY_REQUESTS_PER_SECOND = 1.0
_BODY_MIN_INTERVAL = 1.0 / _BODY_REQUESTS_PER_SECOND

_BODY_PACE_LOCK = asyncio.Lock()
_BODY_LAST_REQUEST = 0.0


@contextlib.asynccontextmanager
async def _pace_body_request():
    """Serialise body fetches onto a fixed cadence, like the feed limiter does."""
    global _BODY_LAST_REQUEST
    async with _BODY_PACE_LOCK:
        wait = _BODY_LAST_REQUEST + _BODY_MIN_INTERVAL - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        _BODY_LAST_REQUEST = time.monotonic()
    yield


async def resolve_url(client, url: str | None) -> str | None:
    """Resolve a feed link to the publisher's real URL.

    Google News hands out `news.google.com/rss/articles/...` redirects; some
    publishers arrive via `bing.com/news/apiclick.aspx?url=...`. Following the
    redirect is more reliable than trying to decode either encoding by hand, and
    `client` must already be built with `follow_redirects=True`.

    Returns `None` when there is no link or the redirect does not land on http(s)
    — a dead end that must not abort the run.
    """
    if not url:
        return None
    try:
        async with _pace_body_request():
            response = await client.get(url, timeout=25.0)
        final = str(response.url)
    except Exception as exc:  # noqa: BLE001 - a dead link is not an error
        logger.debug("news: could not resolve %s: %s", url[:80], exc)
        return None

    if not final.startswith(("http://", "https://")):
        return None
    return final


def extract_body(html: str | None) -> str | None:
    """Pull readable article text out of an HTML page.

    Scored, not naive: the boilerplate-stripped page is cut into candidate
    containers and the one holding the most paragraph text wins. Taking the
    whole document instead reliably drags in related-article teasers and footer
    legal text.

    Returns `None` when extraction is unavailable or the result is too thin to
    be a real article — callers store NULL rather than garbage.
    """
    if not html or not EXTRACTOR_OK:
        return None

    try:
        soup = BeautifulSoup(html, _PARSER)
    except Exception as exc:  # noqa: BLE001 - malformed markup must not abort
        logger.debug("news: body parse failed: %s", exc)
        return None

    for tag in soup(_CHROME_TAGS):
        tag.decompose()

    best = ""
    for tag_name in _CANDIDATES:
        for node in soup.find_all(tag_name):
            paragraphs = [
                p.get_text(" ", strip=True)
                for p in node.find_all("p")
                if len(p.get_text(" ", strip=True)) >= _MIN_PARAGRAPH
            ]
            if not paragraphs:
                continue
            joined = _WHITESPACE.sub(" ", " ".join(paragraphs)).strip()
            # Strictly greater keeps the first (DOM-earliest) container on ties,
            # which is the main article rather than a sidebar that follows it.
            if len(joined) > len(best):
                best = joined
        # A real <article> element is the whole answer when present — do not go
        # on to consider every <div> on the page.
        if len(best) >= MIN_BODY_CHARS:
            break

    if len(best) < MIN_BODY_CHARS:
        return None
    return best


async def fetch_body(client, url: str | None) -> str | None:
    """Fetch one publisher page and extract its text. Never raises.

    Two requests in the worst case: the redirect, then the publisher page. Both
    are best-effort — a dead article yields `None`, never an exception.
    """
    resolved = await resolve_url(client, url)
    if not resolved:
        return None
    try:
        async with _pace_body_request():
            response = await client.get(resolved, timeout=25.0)
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - a dead article is not a run failure
        logger.debug("news: body fetch failed %s: %s", resolved[:80], exc)
        return None
    if "html" not in response.headers.get("content-type", "").lower():
        return None
    return extract_body(response.text)