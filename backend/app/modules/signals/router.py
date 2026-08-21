from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.modules.market_data.service import Interval, Period
from app.modules.signals import service
from app.modules.signals.schemas import (
    MarkerOut,
    RuleOut,
    SignalResponse,
)

router = APIRouter(
    prefix="/signals",
    tags=["signals"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=SignalResponse)
async def signal(
    symbol: str = Query(..., min_length=1, max_length=32),
    interval: Interval = Query("1d"),
    period: Period = Query("2y"),
) -> SignalResponse:
    clean = symbol.strip().upper()
    data = await service.get_signal(clean, interval, period)
    return SignalResponse(
        symbol=clean,
        verdict=data["verdict"],
        score=data["score"],
        confidence=data["confidence"],
        rules=[RuleOut(**r) for r in data["signals"]],
        reasons=data["reasons"],
        markers=[MarkerOut(**m) for m in data["markers"]],
    )
