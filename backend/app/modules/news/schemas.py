from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.news.service import ScrapeStats


class ScrapeRequest(BaseModel):
    """Body for `POST /news/scrape`.

    Deliberately just two fields. One stock at a time and one look-back window
    is the whole contract: concurrency, request rate and symbol batching are
    internal constants chosen from measured upstream behaviour, and exposing them
    only invited configurations that got a 3-year backfill throttled halfway.

    `days` is the look-back window, still sliced one day at a time internally
    because a single wide Google News query silently truncates and loses ~75% of
    its results.
    """

    symbol: str = Field(
        min_length=1,
        max_length=32,
        description="One stock to scrape, e.g. 'RELIANCE.NS' or 'RELIANCE'.",
        examples=["RELIANCE.NS"],
    )
    days: int = Field(
        default=7,
        ge=1,
        le=3650,
        description=(
            "How many days back to collect. One day at a time, so expect "
            "roughly this many requests. Use 7 for the weekly refresh (this "
            "also fills article bodies) and 1095 for the 3-year backfill "
            "(headlines only — bodies are not fetched that far back)."
        ),
        examples=[7],
    )


class ScrapeResult(BaseModel):
    """Outcome of one scrape run."""

    symbol: str = Field(description="The stock that was scraped.")
    articles_seen: int = Field(description="Headlines returned by the source.")
    articles_new: int = Field(description="Rows actually inserted (deduped).")
    duplicates: int = Field(
        description="Headlines skipped because an identical title was already stored."
    )
    rejected: int = Field(description="Headlines dropped by the relevance filter.")
    requests: int = Field(description="HTTP requests made (one per day per query rung).")
    errors: int = 0
    bodies_stored: int = Field(
        default=0,
        description=(
            "Article bodies extracted and stored. Only articles from the last "
            "7 days are eligible, so this is 0 on a long backfill."
        ),
    )
    bodies_failed: int = Field(
        default=0,
        description="Articles whose body could not be extracted (paywall, 404, JS-only page)."
    )
    duration_seconds: float = 0.0

    @classmethod
    def from_stats(cls, stats: ScrapeStats, duration_seconds: float) -> ScrapeResult:
        """Build a response from the scraper's counters.

        Typed explicitly rather than splatting `as_dict()` so mypy can check the
        field types, and so `duration_seconds` stays a single source of truth.
        """
        return cls(
            symbol=stats.symbol,
            articles_seen=stats.articles_seen,
            articles_new=stats.articles_new,
            duplicates=stats.duplicates,
            rejected=stats.rejected,
            requests=stats.requests,
            errors=stats.errors,
            bodies_stored=stats.bodies_stored,
            bodies_failed=stats.bodies_failed,
            duration_seconds=duration_seconds,
        )


class NewsArticleOut(BaseModel):
    """A stored article."""

    id: int
    symbol: str
    title: str
    body: str | None = Field(
        default=None,
        description=(
            "Article text. Null for backfilled rows — bodies are only fetched "
            "for the last 7 days."
        ),
    )
    source: str | None = None
    published_at: datetime | None = None
    url: str | None = None
    fetched_at: datetime


class NewsArticleListResponse(BaseModel):
    symbol: str
    count: int
    articles: list[NewsArticleOut]


class NewsCoverageResponse(BaseModel):
    """Which stocks the scraper covers, and how much has been stored."""

    universe: dict[str, object] = Field(
        description="Provenance of the target universe (source, counts, snapshot date)."
    )
    total_articles: int = Field(description="Rows currently in the news database.")
    symbols_covered: int = Field(description="How many symbols have at least one article.")
    articles_per_symbol: dict[str, int] = Field(default_factory=dict)
