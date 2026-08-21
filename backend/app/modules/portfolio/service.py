from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.portfolio.models import WatchlistItem


async def list_watchlist(db: AsyncSession, user_id: str) -> list[WatchlistItem]:
    result = await db.scalars(
        select(WatchlistItem)
        .where(WatchlistItem.user_id == user_id)
        .order_by(WatchlistItem.sort_order, WatchlistItem.created_at)
    )
    return list(result)


async def get_item(db: AsyncSession, user_id: str, ticker: str) -> WatchlistItem | None:
    return await db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user_id,
            WatchlistItem.ticker == ticker,
        )
    )


async def add_to_watchlist(db: AsyncSession, user_id: str, ticker: str) -> WatchlistItem:
    existing = await get_item(db, user_id, ticker)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{ticker} is already in your watchlist.",
        )
    next_order = await db.scalar(
        select(func.max(WatchlistItem.sort_order)).where(WatchlistItem.user_id == user_id)
    )
    item = WatchlistItem(
        id=str(uuid.uuid4()),
        user_id=user_id,
        ticker=ticker,
        sort_order=(next_order or 0) + 1,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def remove_from_watchlist(db: AsyncSession, user_id: str, ticker: str) -> None:
    item = await get_item(db, user_id, ticker)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{ticker} is not in your watchlist.",
        )
    await db.delete(item)
    await db.commit()
