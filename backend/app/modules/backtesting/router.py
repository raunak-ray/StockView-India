from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.modules.backtesting import service
from app.modules.backtesting.schemas import BacktestRequest, BacktestResponse

router = APIRouter(
    prefix="/backtesting",
    tags=["backtesting"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/strategies")
async def list_strategies() -> dict:
    """List available backtesting strategies."""
    return {
        "strategies": [
            {"name": name, "description": service.STRATEGY_DESCRIPTIONS[name]}
            for name in service.STRATEGIES
        ]
    }


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    body: BacktestRequest,
    user = Depends(get_current_user),
) -> BacktestResponse:
    """Run a backtest for the given symbol and strategy."""
    clean = body.symbol.strip().upper()
    if body.strategy not in service.STRATEGIES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown strategy: {body.strategy}. Use GET /backtesting/strategies.",
        )
    result = await service.run_backtest(
        symbol=clean,
        strategy=body.strategy,
        years=body.years,
        initial_capital=body.initial_capital,
        commission_pct=body.commission_pct,
        sl_pct=body.sl_pct,
        tp_pct=body.tp_pct,
        position_size_pct=body.position_size_pct,
    )
    if not result:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Not enough data to backtest this strategy. Try a longer period.",
        )
    return BacktestResponse(
        symbol=clean,
        strategy=body.strategy,
        **result,
    )
