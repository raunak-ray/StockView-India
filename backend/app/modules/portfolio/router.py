from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.portfolio import paper_service, service
from app.modules.portfolio.schemas import (
    MessageResponse,
    PaperOrderOut,
    PaperOrderRequest,
    PaperPositionOut,
    PaperSummaryResponse,
    WatchlistAddRequest,
    WatchlistItemOut,
    WatchlistResponse,
)

router = APIRouter(
    prefix="/portfolio",
    tags=["portfolio"],
    dependencies=[Depends(get_current_user)],
)


# ── Watchlist endpoints ─────────────────────────────────────────────────────


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


# ── Paper trading endpoints ─────────────────────────────────────────────────


@router.get("/paper", response_model=PaperSummaryResponse)
async def paper_summary(
    user: User = Depends(get_current_user),
) -> PaperSummaryResponse:
    """Portfolio summary: cash, positions, orders, P&L."""
    data = paper_service.get_summary(user.id)
    return PaperSummaryResponse(**data)


@router.post("/paper/order", response_model=PaperOrderOut, status_code=status.HTTP_201_CREATED)
async def paper_place_order(
    body: PaperOrderRequest,
    user: User = Depends(get_current_user),
) -> PaperOrderOut:
    """Execute a paper trade (instant fill at given price)."""
    order = paper_service.place_order(
        user.id,
        symbol=body.symbol,
        side=body.side,
        qty=body.qty,
        price=body.price,
    )
    return PaperOrderOut(**order)


@router.get("/paper/positions", response_model=list[PaperPositionOut])
async def paper_positions(
    user: User = Depends(get_current_user),
) -> list[PaperPositionOut]:
    """Open positions with live P&L."""
    positions = await paper_service.get_positions(user.id)
    return [PaperPositionOut(**p) for p in positions]


@router.get("/paper/orders", response_model=list[PaperOrderOut])
async def paper_orders(
    user: User = Depends(get_current_user),
) -> list[PaperOrderOut]:
    """Order history (newest first)."""
    orders = paper_service.get_orders(user.id)
    return [PaperOrderOut(**o) for o in orders]


@router.post("/paper/reset", response_model=PaperSummaryResponse)
async def paper_reset(
    user: User = Depends(get_current_user),
) -> PaperSummaryResponse:
    """Reset portfolio to ₹1,00,000 starting cash."""
    data = paper_service.reset_portfolio(user.id)
    return PaperSummaryResponse(**data)
