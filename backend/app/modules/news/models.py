from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.news_db import NewsBase


class NewsArticle(NewsBase):
    """A single scraped article (news_articles).

    Lives in the isolated news database, never in the app database.

    Dedupe strategy: `content_hash` is a sha256 of the *normalised* title
    (lowercased, publisher suffix and punctuation stripped). Google News
    re-syndicates the same headline across many outlets, and the weekly crawl
    overlaps itself by design — so `(content_hash, symbol)` is UNIQUE and every
    insert is an ON CONFLICT DO NOTHING. Re-running the scraper is therefore
    free and idempotent.

    `body` holds the article text, extracted from the publisher page. No feed
    carries it, so it costs a second HTTP request per article and is therefore
    only populated for the recent window (see `service.BODY_FILL_DAYS`) — the
    3-year backfill deliberately stores headline-only rows. NULL body is a
    normal, expected state, not a failure.
    """

    __tablename__ = "news_articles"
    __table_args__ = (
        # The dedupe guarantee. Same headline for the same symbol is stored once.
        UniqueConstraint("content_hash", "symbol", name="uq_news_article_hash_symbol"),
        # Serves the stock-page feed: newest articles for one symbol.
        Index("ix_news_article_symbol_published", "symbol", "published_at"),
        # Serves "biggest stories across the market" / daily rollups.
        Index("ix_news_article_published", "published_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Yahoo-style ticker with exchange suffix (RELIANCE.NS). Matches the
    # `ticker` format used by watchlist_items so the two can be joined.
    symbol: Mapped[str] = mapped_column(String(32), index=True)

    title: Mapped[str] = mapped_column(Text)

    # Article text, scraped from the publisher page. NULL for headline-only rows.
    body: Mapped[str | None] = mapped_column(Text)

    source: Mapped[str | None] = mapped_column(String(128))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    url: Mapped[str | None] = mapped_column(Text)

    # sha256 of the normalised title; see class docstring.
    content_hash: Mapped[str] = mapped_column(String(64))

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
