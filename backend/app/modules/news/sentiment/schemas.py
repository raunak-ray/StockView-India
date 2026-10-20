from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class SentimentCounts(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0


class SentimentWindow(BaseModel):
    start: datetime | None = None
    end: datetime | None = None


class ExtremesHeadline(BaseModel):
    title: str
    score: float
    source: str | None = None
    published_at: str | None = None
    url: str | None = None


class StockSentimentOut(BaseModel):
    """Stored summary for one stock.

    `coverage` is the honesty field: a stock with no stored articles returns
    `coverage="none"` rather than a fabricated NEUTRAL, and `article_count`
    tells the reader how much evidence the score rests on.
    """

    symbol: str
    score: float = 0.0
    label: str = "NEUTRAL"
    coverage: str = Field(
        description="'available' when scored from real articles, 'none' when there is no data."
    )
    article_count: int = 0
    counts: SentimentCounts = Field(default_factory=SentimentCounts)
    avg_confidence: float = 0.0
    window: SentimentWindow = Field(default_factory=SentimentWindow)
    top_positive: list[ExtremesHeadline] = Field(default_factory=list)
    top_negative: list[ExtremesHeadline] = Field(default_factory=list)
    model_version: str | None = None
    updated_at: datetime | None = None


class DailySentimentPoint(BaseModel):
    day: date
    article_count: int = 0
    mean_score: float = 0.0
    pos_count: int = 0
    neu_count: int = 0
    neg_count: int = 0


class SentimentHistoryOut(BaseModel):
    symbol: str
    days: int
    coverage: str = "available"
    points: list[DailySentimentPoint] = Field(default_factory=list)


class ScoredArticleOut(BaseModel):
    """One stored headline with its stored score."""

    id: int
    title: str
    source: str | None = None
    published_at: datetime | None = None
    url: str | None = None
    score: float = 0.0
    label: str = "NEUTRAL"


class ScoredArticleListOut(BaseModel):
    symbol: str
    count: int
    coverage: str = "available"
    articles: list[ScoredArticleOut] = Field(default_factory=list)


class RankingEntry(BaseModel):
    symbol: str
    score: float
    label: str
    article_count: int


class RankingOut(BaseModel):
    count: int
    ranking: list[RankingEntry] = Field(default_factory=list)


class ScoringStatusOut(BaseModel):
    """How much of the corpus has been scored — read from both databases."""

    articles_total: int
    articles_scored: int
    articles_pending: int
    symbols_summarised: int
    period_rows: int
    model_versions: dict[str, int] = Field(default_factory=dict)


class ScoreRunOut(BaseModel):
    unscored_seen: int = 0
    scored: int = 0
    skipped_existing: int = 0
    keyword_fallback: int = 0
    symbols_aggregated: int | None = None
    period_rows_aggregated: int | None = None
    priced_symbols: int | None = None
    duration_seconds: float = 0.0

    @classmethod
    def build(
        cls,
        stats: dict[str, Any],
        duration: float,
        aggregate: dict[str, Any] | None = None,
    ) -> ScoreRunOut:
        return cls(
            unscored_seen=stats.get("unscored_seen", 0),
            scored=stats.get("scored", 0),
            skipped_existing=stats.get("skipped_existing", 0),
            keyword_fallback=stats.get("keyword_fallback", 0),
            symbols_aggregated=(aggregate or {}).get("symbols"),
            period_rows_aggregated=(aggregate or {}).get("period_rows"),
            priced_symbols=(aggregate or {}).get("priced_symbols"),
            duration_seconds=duration,
        )

# ── Sentiment vs price comparison ───────────────────────────────────────────
# One response for the whole chart. Every period is returned at once because the
# UI has a period switcher, and four round trips means four chances to render a
# half-drawn chart. Period keys are fixed ("1m"/"3m"/"1y"/"3y") and are always
# present, so the frontend never has to guard for a missing key.


class TrendSeriesPoint(BaseModel):
    """One bucket: sentiment and close on a shared date.

    `sentiment` is null in a bucket that had a price but no articles, which is
    the normal case at 3Y granularity. Plotting a gap is correct there —
    interpolating would invent coverage that does not exist.
    """

    date: str
    sentiment: float | None = None
    article_count: int = 0
    avg_confidence: float = 0.0
    pos_count: int = 0
    close: float | None = None


class TrendSentiment(BaseModel):
    score: float | None = None
    label: str = "NO_DATA"
    article_count: int = 0
    pos_count: int = 0
    neu_count: int = 0
    neg_count: int = 0
    avg_confidence: float = 0.0
    change: float | None = Field(
        default=None, description="First bucket mean minus last bucket mean."
    )
    window_start: str | None = None
    window_end: str | None = None


class TrendPrice(BaseModel):
    start: float | None = None
    end: float | None = None
    change_pct: float | None = None
    currency: str = "INR"


class TrendPeriod(BaseModel):
    label: str
    days: int
    granularity: str = Field(description="'day', 'week' or 'month'.")
    sentiment: TrendSentiment
    price: TrendPrice
    series: list[TrendSeriesPoint] = Field(default_factory=list)


class TrendOut(BaseModel):
    """Everything the comparison graph needs, for all four periods."""

    symbol: str
    model_version: str
    generated_at: str
    as_of: str
    has_coverage: bool
    periods: dict[str, TrendPeriod]
