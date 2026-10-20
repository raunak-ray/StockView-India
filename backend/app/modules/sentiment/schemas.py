from datetime import datetime

from pydantic import BaseModel, Field


class NewsResponse(BaseModel):
    symbol: str
    count: int
    headlines: list[str]


class HeadlineSentiment(BaseModel):
    headline: str
    label: str
    conf: float
    score: float


class NewsSentiment(BaseModel):
    score: float
    label: str
    detail: list[HeadlineSentiment]


class TechnicalSignal(BaseModel):
    name: str
    tone: str
    message: str
    weight: float


class TechnicalSentiment(BaseModel):
    score: float
    label: str
    raw_score: float
    signals: list[TechnicalSignal]


class SentimentScoreResponse(BaseModel):
    symbol: str
    finbert_available: bool = Field(description="Whether the FinBERT model is installed")
    news: NewsSentiment
    technical: TechnicalSentiment


# ── Insight (the endpoint the frontend uses) ─────────────────────────────────
# One payload for the news-and-mood card of a stock page: the stored sentiment
# when we have it, the live headlines when we do not.


class InsightCounts(BaseModel):
    """How many articles landed on each side."""

    positive: int = 0
    neutral: int = 0
    negative: int = 0


class InsightWindow(BaseModel):
    """The window the stored score actually covers."""

    start: datetime | str | None = None
    end: datetime | str | None = None


class InsightNews(BaseModel):
    """The news half of the payload.

    `article_count` is the trust signal: a score built from 4 headlines must
    not look like one built on 1,600 articles.
    """

    score: float = 0.0
    label: str = "NEUTRAL"
    article_count: int = 0
    counts: InsightCounts = Field(default_factory=InsightCounts)
    avg_confidence: float = 0.0
    window: InsightWindow = Field(default_factory=InsightWindow)
    detail: list[HeadlineSentiment] = Field(default_factory=list)


class StoredArticle(BaseModel):
    """One stored headline with its stored score."""

    id: int | None = None
    title: str
    source: str | None = None
    published_at: datetime | str | None = None
    url: str | None = None
    score: float = 0.0
    label: str = "NEUTRAL"


class SentimentPeriodCard(BaseModel):
    """One period card (1M / 3M / 1Y / 3Y).

    `available` is False when we stored nothing for that window. The score is
    null in that case rather than a measured-looking zero.
    """

    period: str
    title: str
    days: int = 0
    available: bool = False
    score: float | None = None
    label: str = "NO_DATA"
    article_count: int = 0
    pos_count: int = 0
    neu_count: int = 0
    neg_count: int = 0
    avg_confidence: float = 0.0
    sentiment_change: float | None = None
    window_start: str | None = None
    window_end: str | None = None
    price_start: float | None = None
    price_end: float | None = None
    price_change_pct: float | None = None


class SentimentInsightResponse(BaseModel):
    """Everything the news-and-mood card needs, in one call.

    `isStoredData` says where the news numbers came from:
      * True  — our archive. The score, the period breakdown, the strongest
        stories and the recent articles are all pre-computed.
      * False — nothing stored for this stock, so the headlines were scraped
        and scored live. The period breakdown is empty in that case.
    """

    symbol: str
    isStoredData: bool = Field(
        description=(
            "True when the news numbers came from the stored archive, "
            "False for a live scrape."
        )
    )
    source: str = Field(description="'stored' or 'live'.")
    news: InsightNews
    technical: TechnicalSentiment
    periods: dict[str, SentimentPeriodCard] = Field(default_factory=dict)
    top_articles: list[StoredArticle] = Field(default_factory=list)
    top_positive: list[StoredArticle] = Field(default_factory=list)
    top_negative: list[StoredArticle] = Field(default_factory=list)
    model_version: str | None = None
    updated_at: str | None = None
    generated_at: str


class DeprecatedResponse(BaseModel):
    """What the old endpoints answer with now."""

    deprecated: bool = True
    message: str
    replacement: str
    symbol: str | None = None
