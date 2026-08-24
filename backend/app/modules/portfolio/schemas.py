from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ── Watchlist schemas (existing) ────────────────────────────────────────────


class WatchlistAddRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=32, examples=["RELIANCE.NS"])


class WatchlistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    sort_order: int
    created_at: datetime


class WatchlistResponse(BaseModel):
    count: int
    items: list[WatchlistItemOut]


class MessageResponse(BaseModel):
    message: str


# ── Paper trading schemas ───────────────────────────────────────────────────


class PaperSummaryResponse(BaseModel):
    cash: float
    positions_count: int
    orders_count: int
    pnl: float
    initial_cash: float


class PaperOrderRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=32, examples=["RELIANCE.NS"])
    side: str = Field(..., pattern="^(BUY|SELL)$")
    qty: int = Field(..., gt=0, le=100_000)
    price: float = Field(..., gt=0, le=10_00_000)


class PaperOrderOut(BaseModel):
    id: str
    ts: str
    symbol: str
    type: str
    qty: int
    price: float
    value: float
    mode: str


class PaperPositionOut(BaseModel):
    symbol: str
    qty: int
    avg_cost: float
    ltp: float
    unrealised_pnl: float
    pnl_pct: float
