from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.modules.market_data.service import Interval, Period
from app.modules.smc import service
from app.modules.smc.schemas import SmcResponse

router = APIRouter(
    prefix="/smc",
    tags=["smc"],
    dependencies=[Depends(get_current_user)],
)

# Defaults + slider ranges mirror the Streamlit controls (app.py:1009-1011).


@router.get("", response_model=SmcResponse)
async def smc(
    symbol: str = Query(..., min_length=1, max_length=32),
    interval: Interval = Query("1d"),
    period: Period = Query("2y"),
    swing_len: int = Query(50, ge=5, le=100),
    int_len: int = Query(5, ge=2, le=20),
    ob_count: int = Query(3, ge=1, le=10),
) -> SmcResponse:
    clean = symbol.strip().upper()
    data = await service.get_smc(
        clean, interval, period,
        swing_len=swing_len, int_len=int_len, ob_count=ob_count,
    )
    return SmcResponse(symbol=clean, interval=interval, period=period, **data)
