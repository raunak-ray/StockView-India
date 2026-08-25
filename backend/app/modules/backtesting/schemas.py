from __future__ import annotations

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=32, examples=["RELIANCE.NS"])
    strategy: str = Field(..., description="Strategy name")
    years: int = Field(5, ge=1, le=10)
    initial_capital: float = Field(100_000.0, ge=10_000, le=10_000_000)
    commission_pct: float = Field(0.1, ge=0.0, le=1.0)
    sl_pct: float = Field(5.0, ge=0.0, le=20.0, description="Stop-loss % (0 = none)")
    tp_pct: float = Field(0.0, ge=0.0, le=50.0, description="Take-profit % (0 = none)")
    position_size_pct: float = Field(100.0, ge=10, le=100)


class TradeOut(BaseModel):
    entry_date: str
    exit_date: str
    entry_px: float
    exit_px: float
    shares: float
    pnl: float
    pnl_pct: float
    hold_days: int
    exit_reason: str
    win: bool


class MonthlyReturn(BaseModel):
    month: str
    return_pct: float


class BacktestResponse(BaseModel):
    symbol: str
    strategy: str
    final_equity: float
    total_ret_pct: float
    cagr: float
    sharpe: float
    sortino: float
    calmar: float
    max_dd: float
    dd_dur_days: int
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float | None
    expectancy: float
    expectancy_pct: float
    avg_hold: float
    years: float
    bh_ret: float
    bh_cagr: float
    alpha: float
    initial_capital: float
    equity_curve: list[dict]
    trades: list[TradeOut]
    monthly_returns: list[MonthlyReturn]
