"""Second, isolated database connection for scraped news articles.

News is the bulkiest and fastest-growing data in the project, so it lives in
its own Postgres database (its own Neon *project* in hosted deployments —
storage is metered per project, not per database, so a second database inside
the same project would share the same allowance).

Everything about this module mirrors `app/core/db.py` deliberately:
  - same `_normalise_db_url` SSL fix-up (asyncpg rejects libpq query params)
  - same engine options and `pool_pre_ping` behaviour
  - its own `DeclarativeBase`, so `init_db()` on the main app never creates
    news tables in the app database and vice versa

Usage:
    from app.core.news_db import NewsSessionLocal, init_news_db, ping_news_db
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.db import _normalise_db_url


def _force_async_driver(url: str) -> str:
    """Pin the asyncpg driver.

    Neon console copy-paste yields `postgresql://…`, which SQLAlchemy resolves to
    the **sync** psycopg2 driver — not installed here, and unusable from async
    code. We are async-only, so any bare `postgresql://` becomes
    `postgresql+asyncpg://`. An explicit driver already in the URL is left alone.
    """
    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


news_database_url, news_connect_args = _normalise_db_url(
    _force_async_driver(settings.news_db_url)
)

news_engine = create_async_engine(
    news_database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=news_connect_args,
)
NewsSessionLocal = async_sessionmaker(news_engine, class_=AsyncSession, expire_on_commit=False)


class NewsBase(DeclarativeBase):
    """Declarative base for the news database.

    Deliberately separate from `app.core.db.Base` — mixing them would put news
    tables in the app database on `init_db()`.
    """


async def get_news_db() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency yielding a news-database session."""
    async with NewsSessionLocal() as session:
        yield session


async def init_news_db() -> None:
    """Create every table declared in the news models (idempotent)."""
    from app.modules.news import models as news_models  # noqa: F401

    async with news_engine.begin() as conn:
        await conn.run_sync(NewsBase.metadata.create_all)


async def ping_news_db() -> None:
    """Fail fast if the news database is unreachable."""
    async with news_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def close_news_db() -> None:
    """Dispose the news engine pool (called on app shutdown)."""
    await news_engine.dispose()
