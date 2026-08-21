from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.portfolio import service
from app.modules.portfolio.schemas import (
    MessageResponse,
    WatchlistAddRequest,
    WatchlistItemOut,
    WatchlistResponse,
)

router = APIRouter(
    prefix="/portfolio",
    tags=["portfolio"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/watchlist", response_model=WatchlistResponse)
async def get_watchlist(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WatchlistResponse:
    items = await service.list_watchlist(db, user.id)
    return WatchlistResponse(
        count=len(items),
        items=[WatchlistItemOut.model_validate(i) for i in items],
    )


@router.post("/watchlist", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    body: WatchlistAddRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    ticker = body.ticker.strip().upper()
    await service.add_to_watchlist(db, user.id, ticker)
    return MessageResponse(message=f"{ticker} added to your watchlist.")


@router.delete("/watchlist/{ticker}", response_model=MessageResponse)
async def remove_from_watchlist(
    ticker: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    clean = ticker.strip().upper()
    await service.remove_from_watchlist(db, user.id, clean)
    return MessageResponse(message=f"{clean} removed from your watchlist.")
