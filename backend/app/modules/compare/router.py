from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.modules.compare.schemas import CompareResponse
from app.modules.compare.service import compare_symbols

compare_router = APIRouter(
    prefix="/compare",
    tags=["compare"],
    dependencies=[Depends(get_current_user)],
)


@compare_router.get("", response_model=CompareResponse)
async def compare(
    symbols: str = Query(..., description="Comma-separated, 2-4 symbols"),
    period: str = Query("1y", description="1mo, 3mo, 6mo, 1y, 3y, 5y"),
) -> CompareResponse:
    syms = [s.strip() for s in symbols.split(",") if s.strip()]
    if len(syms) < 2:
        from fastapi import HTTPException
        raise HTTPException(400, "Provide at least 2 comma-separated symbols")
    if len(syms) > 4:
        from fastapi import HTTPException
        raise HTTPException(400, "Maximum 4 symbols allowed")
    result = await compare_symbols(syms, period)
    return CompareResponse(**result)
