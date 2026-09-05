from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def _normalise_db_url(url: str) -> tuple[str, dict]:
    """Strip SSL-related query params from the asyncpg URL and translate
    them into `connect_args` asyncpg understands.

    asyncpg does not understand `?sslmode=...` in the URL — those get
    passed to `connect()` as kwargs and fail with
    `TypeError: connect() got an unexpected keyword argument 'sslmode'`.

    This function:
      1. Strips `sslmode`, `channel_binding`, and similar pg-libpq
         params from the URL.
      2. Returns the cleaned URL and the appropriate `connect_args`
         (`{"ssl": True}` for `require` / `verify-ca` / `verify-full`).
    """
    parsed = urlparse(url)
    if not parsed.query:
        return url, {}

    params = parse_qs(parsed.query, keep_blank_values=True)
    sslmode = params.pop("sslmode", [None])[0]
    # asyncpg does not support channel_binding — drop it too.
    params.pop("channel_binding", None)

    # Rebuild the query string without the SSL params.
    new_query = urlencode({k: v[0] for k, v in params.items()}, doseq=False)
    new_url = urlunparse(parsed._replace(query=new_query))

    # Translate sslmode to asyncpg's `ssl` kwarg.
    connect_args: dict = {}
    if sslmode in ("require", "verify-ca", "verify-full"):
        connect_args["ssl"] = True
    # For "disable" / "allow" / "prefer" / None we don't set anything.

    return new_url, connect_args


database_url, db_connect_args = _normalise_db_url(settings.database_url)

engine = create_async_engine(
    database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=db_connect_args,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    from app.modules.auth import models  # noqa: F401
    from app.modules.portfolio import models as portfolio_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def ping_db() -> None:
    """Fail fast if Postgres is unreachable (used by /readyz)."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
