"""Stored sentiment for scraped news.

Three tables, deliberately split across two databases:

  * ``NewsArticleSentiment``  -> news DB. One row per article, sitting beside
    the headline it describes. The source of truth: every number the app shows
    is derived from this, so re-tuning the blend never requires re-scraping.
  * ``StockNewsSentiment``    -> main app DB. One row per stock. What the API
    reads for "how bullish is this stock right now", so the hot path never
    touches the news database.
  * ``NewsSentimentPeriod``   -> main app DB. One row per stock per period
    (1M / 3M / 1Y / 3Y), the shape the comparison chart plots. Materialised from
    the first table plus the price feed, so it is rebuildable and disposable.

Why all three probabilities are stored: the legacy pipeline collapsed FinBERT's
output to a single signed number, which is irreversible — you cannot recover
"this was 60% positive" from "+0.30". Keeping pos/neu/neg means the 70/30
blend can be re-tuned later without re-running the model over 170k headlines.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.news_db import NewsBase


class NewsArticleSentiment(NewsBase):
    """FinBERT result for one stored headline (news database).

    Written exactly once by the offline scorer. Never recomputed at request
    time — that is the entire point of this phase.
    """

    __tablename__ = "news_article_sentiment"

    article_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("news_articles.id", ondelete="CASCADE"), primary_key=True
    )
    # Denormalised so per-symbol rollups never need to join news_articles.
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    finbert_pos: Mapped[float] = mapped_column(Float)
    finbert_neu: Mapped[float] = mapped_column(Float)
    finbert_neg: Mapped[float] = mapped_column(Float)
    finbert_label: Mapped[str] = mapped_column(String(10), index=True)

    # Kept so the blend can be re-weighted without re-running FinBERT.
    keyword_score: Mapped[float] = mapped_column(Float, default=0.0)

    # The number the app actually serves: 0.70 * FinBERT + 0.30 * keyword.
    final_score: Mapped[float] = mapped_column(Float, index=True)

    # FinBERT confidence in the winning class (max of the three).
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # "prosusai-finbert" or "keyword_only" — makes an absent model visible
    # instead of silently producing a keyword number wearing FinBERT's name.
    model_version: Mapped[str] = mapped_column(String(32), default="prosusai-finbert")

    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("ix_news_sentiment_symbol_published", "symbol", "published_at"),
    )


class StockNewsSentiment(Base):
    """One row per stock — the app-facing summary (main database).

    Sized for the app, not the corpus: ~86 rows for the whole Nifty 100
    intersection. ``article_count`` is the trust signal — a score built from 4
    headlines must not look like one built from 1,600.
    """

    __tablename__ = "stock_news_sentiment"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)

    score: Mapped[float] = mapped_column(Float, default=0.0)
    label: Mapped[str] = mapped_column(String(10), default="NEUTRAL", index=True)

    article_count: Mapped[int] = mapped_column(Integer, default=0)
    pos_count: Mapped[int] = mapped_column(Integer, default=0)
    neu_count: Mapped[int] = mapped_column(Integer, default=0)
    neg_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # What window the score actually covers, so the UI can say "based on
    # 1,605 articles, Oct 2023 - Oct 2026" instead of implying "today".
    window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # The extremes, for the "biggest stories" panel and the chatbot. Titles only
    # — no article bodies are fetched anywhere in this project.
    top_positive: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    top_negative: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

    model_version: Mapped[str] = mapped_column(String(32), default="prosusai-finbert")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class NewsSentimentPeriod(Base):
    """Per-stock, per-period rollup — the shape the UI actually charts.

    Replaces a per-day table. A daily row for 86 stocks over three years is
    ~94k rows that the app never reads directly: the chart shows 1M / 3M / 1Y / 3Y
    buckets, so storing a day per row bought nothing and made every aggregate a
    scan. Four rows per stock is the whole requirement, and the buckets are
    named by a key the frontend can switch on directly.

    Sentiment comes from ``NewsArticleSentiment`` (news DB) and price from the
    market-data module, so this table is a **materialised summary** — the source
    of truth for both is elsewhere and this can be rebuilt at any time with
    ``aggregate_periods``. ``price_*`` columns are nullable because sentiment
    scoring and price fetching fail independently, and a stock with news but no
    reachable quote should still chart its sentiment.
    """

    __tablename__ = "news_sentiment_period"
    # `label` is indexed via `index=True` on the column below; declaring it here
    # as well produced a duplicate CREATE INDEX with the same name.

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    # "1m" | "3m" | "1y" | "3y" — see service.PERIODS for the canonical set.
    period: Mapped[str] = mapped_column(String(4), primary_key=True)

    days: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    label: Mapped[str] = mapped_column(String(10), default="NEUTRAL", index=True)

    article_count: Mapped[int] = mapped_column(Integer, default=0)
    pos_count: Mapped[int] = mapped_column(Integer, default=0)
    neu_count: Mapped[int] = mapped_column(Integer, default=0)
    neg_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # First-bucket mean minus last-bucket mean: did coverage warm or cool over
    # the window? Distinct from `score`, which is the whole-window average.
    sentiment_change: Mapped[float] = mapped_column(Float, default=0.0)

    # Nullable: price comes from a separate upstream that can fail on its own.
    price_start: Mapped[float | None] = mapped_column(Float)
    price_end: Mapped[float | None] = mapped_column(Float)
    price_change_pct: Mapped[float | None] = mapped_column(Float)

    model_version: Mapped[str] = mapped_column(String(32), default="prosusai-finbert")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )