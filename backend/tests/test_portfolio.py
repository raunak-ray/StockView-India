from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base
from app.modules.auth.models import User
from app.modules.portfolio import service

TEST_DATABASE_URL = os.environ.get(
    "SV_TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/stockview_test",
)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        session.add(User(id="u1", username="demo", password_hash="x", role="user"))
        await session.commit()
        yield session
    await engine.dispose()


async def test_add_list_remove_roundtrip(db: AsyncSession):
    await service.add_to_watchlist(db, "u1", "RELIANCE.NS")
    await service.add_to_watchlist(db, "u1", "TCS.NS")

    items = await service.list_watchlist(db, "u1")
    assert [i.ticker for i in items] == ["RELIANCE.NS", "TCS.NS"]
    assert items[0].sort_order < items[1].sort_order

    await service.remove_from_watchlist(db, "u1", "RELIANCE.NS")
    items = await service.list_watchlist(db, "u1")
    assert [i.ticker for i in items] == ["TCS.NS"]


async def test_add_duplicate_raises_409(db: AsyncSession):
    await service.add_to_watchlist(db, "u1", "TCS.NS")
    with pytest.raises(HTTPException) as exc:
        await service.add_to_watchlist(db, "u1", "TCS.NS")
    assert exc.value.status_code == 409


async def test_remove_missing_raises_404(db: AsyncSession):
    with pytest.raises(HTTPException) as exc:
        await service.remove_from_watchlist(db, "u1", "NOPE.NS")
    assert exc.value.status_code == 404


async def test_watchlists_are_per_user(db: AsyncSession):
    await db.merge(User(id="u2", username="admin", password_hash="x", role="admin"))
    await db.commit()
    await service.add_to_watchlist(db, "u1", "INFY.NS")

    other = await service.list_watchlist(db, "u2")
    assert other == []
