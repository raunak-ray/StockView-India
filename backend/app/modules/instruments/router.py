from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.modules.instruments import service
from app.modules.instruments.schemas import (
    Instrument,
    InstrumentListResponse,
    InstrumentSearchResponse,
)

router = APIRouter(
    prefix="/instruments",
    tags=["instruments"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=InstrumentListResponse)
async def list_instruments() -> InstrumentListResponse:
    instruments = [
        Instrument(name=name, ticker=ticker)
        for name, ticker in service.all_stocks().items()
    ]
    return InstrumentListResponse(count=len(instruments), instruments=instruments)


@router.get("/search", response_model=InstrumentSearchResponse)
async def search_instruments(
    q: str = Query(..., min_length=1, max_length=64, description="Name or ticker substring"),
    limit: int = Query(50, ge=1, le=200),
) -> InstrumentSearchResponse:
    results = service.search_stocks(q, limit=limit)
    instruments = [Instrument.model_validate(r) for r in results]
    return InstrumentSearchResponse(query=q, count=len(instruments), results=instruments)
