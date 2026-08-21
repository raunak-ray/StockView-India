from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.modules.market_data import service
from app.modules.market_data.schemas import (
    Candle,
    GainersLosersResponse,
    HistoryResponse,
    IndexQuote,
    InfoResponse,
    MarketSummaryResponse,
    Mover,
    QuoteResponse,
)

router = APIRouter(
    prefix="/market",
    tags=["market-data"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/history", response_model=HistoryResponse)
async def history(
    symbol: str = Query(..., min_length=1, max_length=32,
                       description="Yahoo ticker, e.g. RELIANCE.NS"),
    interval: service.Interval = Query("1d"),
    period: service.Period = Query("2y"),
) -> HistoryResponse:
    candles = await service.get_history(symbol.strip().upper(), interval, period)
    return HistoryResponse(
        symbol=symbol, interval=interval, period=period,
        count=len(candles), candles=[Candle(**c) for c in candles],
    )


@router.get("/quote", response_model=QuoteResponse)
async def quote(
    symbol: str = Query(..., min_length=1, max_length=32),
) -> QuoteResponse:
    data = await service.get_quote(symbol.strip().upper())
    return QuoteResponse(symbol=symbol, **data)


@router.get("/info", response_model=InfoResponse)
async def info(
    symbol: str = Query(..., min_length=1, max_length=32),
) -> InfoResponse:
    data = await service.get_info(symbol.strip().upper())
    return InfoResponse(symbol=symbol, info=data)


@router.get("/market-summary", response_model=MarketSummaryResponse)
async def market_summary() -> MarketSummaryResponse:
    indices = await service.get_market_summary()
    return MarketSummaryResponse(indices=[IndexQuote(**i) for i in indices])


@router.get("/gainers-losers", response_model=GainersLosersResponse)
async def gainers_losers() -> GainersLosersResponse:
    data = await service.get_gainers_losers()
    return GainersLosersResponse(
        gainers=[Mover(**m) for m in data["gainers"]],
        losers=[Mover(**m) for m in data["losers"]],
    )
