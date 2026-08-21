from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


class HistoryResponse(BaseModel):
    symbol: str
    interval: str
    period: str
    count: int
    candles: list[Candle]


class QuoteResponse(BaseModel):
    symbol: str
    price: float
    previous_close: float | None = None
    change: float | None = None
    change_pct: float | None = None


class InfoResponse(BaseModel):
    symbol: str
    info: dict[str, Any]


class IndexQuote(BaseModel):
    name: str
    symbol: str
    price: float
    change: float
    change_pct: float


class MarketSummaryResponse(BaseModel):
    indices: list[IndexQuote]


class Mover(BaseModel):
    symbol: str
    price: float
    change: float
    change_pct: float


class GainersLosersResponse(BaseModel):
    gainers: list[Mover]
    losers: list[Mover]
