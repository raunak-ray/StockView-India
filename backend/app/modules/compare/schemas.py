from __future__ import annotations

from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    symbols: list[str] = Field(..., min_length=2, max_length=4, description="2-4 symbols")
    period: str = Field("1y", description="1mo, 3mo, 6mo, 1y, 3y, 5y")


class SymbolSnapshot(BaseModel):
    symbol: str
    name: str
    last_price: float
    change_pct: float
    volume: int
    market_cap: float | None = None
    pe_ratio: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None


class NormalizedPoint(BaseModel):
    date: str
    values: dict[str, float]


class CompareResponse(BaseModel):
    symbols: list[SymbolSnapshot]
    normalized: list[NormalizedPoint]
    period: str
