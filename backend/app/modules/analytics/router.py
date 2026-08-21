from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.modules.analytics import service
from app.modules.analytics.schemas import (
    IndicatorsResponse,
    SeriesPoint,
    SupportResistanceResponse,
)
from app.modules.market_data.service import Interval, Period

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(get_current_user)],
)

_COLUMN_MAP = {
    "sma20": "SMA_20", "sma50": "SMA_50", "ema20": "EMA_20",
    "bb_high": "BB_H", "bb_mid": "BB_M", "bb_low": "BB_L",
    "rsi": "RSI", "atr": "ATR",
    "macd": "MACD", "macd_signal": "M_SIG", "macd_hist": "M_HIS",
}


@router.get("/indicators", response_model=IndicatorsResponse)
async def indicators(
    symbol: str = Query(..., min_length=1, max_length=32),
    interval: Interval = Query("1d"),
    period: Period = Query("2y"),
) -> IndicatorsResponse:
    clean = symbol.strip().upper()
    raw = await service.get_indicators(clean, interval, period)
    data = {
        field: [SeriesPoint(**p) for p in raw.get(column.lower(), [])]
        for field, column in _COLUMN_MAP.items()
    }
    return IndicatorsResponse(
        symbol=clean, interval=interval, period=period, **data
    )


@router.get("/support-resistance", response_model=SupportResistanceResponse)
async def support_resistance(
    symbol: str = Query(..., min_length=1, max_length=32),
    interval: Interval = Query("1d"),
    period: Period = Query("2y"),
) -> SupportResistanceResponse:
    clean = symbol.strip().upper()
    return SupportResistanceResponse(
        **await service.get_support_resistance(clean, interval, period)
    )
