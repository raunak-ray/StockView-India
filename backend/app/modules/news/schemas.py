from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.news.service import ScrapeStats


class ScrapeRequest(BaseModel):
    """Body for `POST /news/scrape`.

    `days` is the look-back window **per symbol**. The scraper still slices that
    window one day at a time internally, because a single wide Google News
    query silently truncates and loses most of its results.
    """

    days: int = Field(
        default=7,
        ge=1,
        le=3650,
        description=(
            "How many days back to collect, per symbol. The window is walked "
            "one day at a time so recall is complete — a single wide query "
            "truncates and loses ~75% of results. Use 7 for the weekly "
            "incremental refresh, 1095 for the one-time 3-year backfill."
        ),
    )
    symbols: list[str] | None = Field(
        default=None,
        description=(
            "Optional subset of symbols to scrape (e.g. ['RELIANCE.NS','TCS']). "
            "Omit to scrape the whole Nifty 100 universe."
        ),
    )
    max_symbols: int | None = Field(
        default=None,
        ge=1,
        le=100,
        description="Optional cap on how many symbols to process this call.",
    )
    concurrency: int = Field(
        default=12,
        ge=1,
        le=32,
        description="Max simultaneous HTTP requests. Affects runtime, not throttling.",
    )


class ScrapeResult(BaseModel):
    """Outcome of one scrape run."""

    articles_seen: int = Field(description="Headlines returned by the sources.")
    articles_new: int = Field(description="Rows actually inserted (deduped).")
    duplicates: int = Field(
        description="Headlines skipped because an identical title was already stored."
    )
    rejected: int = Field(description="Headlines dropped by the relevance filter.")
    requests: int = Field(description="HTTP requests made (days x symbols).")
    errors: int = 0
    symbols_processed: int = 0
    per_symbol: dict[str, int] = Field(
        default_factory=dict, description="Inserted article count per symbol."
    )
    duration_seconds: float = 0.0

    @classmethod
    def from_stats(cls, stats: ScrapeStats, duration_seconds: float) -> ScrapeResult:
        """Build a response from the scraper's counters.

        Typed explicitly rather than splatting `as_dict()` so mypy can check the
        field types, and so `duration_seconds` stays a single source of truth.
        """
        return cls(
            articles_seen=stats.articles_seen,
            articles_new=stats.articles_new,
            duplicates=stats.duplicates,
            rejected=stats.rejected,
            requests=stats.requests,
            errors=stats.errors,
            symbols_processed=len(stats.per_symbol),
            per_symbol=dict(stats.per_symbol),
            duration_seconds=duration_seconds,
        )


class NewsArticleOut(BaseModel):
    """A stored headline."""

    id: int
    symbol: str
    title: str
    source: str | None = None
    published_at: datetime | None = None
    url: str | None = None
    query_used: str | None = None
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
